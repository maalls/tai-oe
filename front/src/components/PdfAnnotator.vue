<template>
   <div class="flex flex-col w-full h-screen bg-white rounded-lg shadow">
      <!-- Toolbar -->
      <div class="flex items-center gap-2 p-3 border-b border-gray-200">
         <button
            type="button"
            @click="clearAnnotations"
            class="px-3 py-2 bg-red-500 hover:bg-red-600 disabled:bg-gray-300 text-white rounded text-sm font-medium"
         >
            Clear
         </button>
         <div class="flex gap-2 ml-auto">
            <button
               @click="zoomOut"
               class="px-2 py-1 bg-gray-200 hover:bg-gray-300 text-sm rounded"
            >
               −
            </button>
            <span class="px-3 py-1 text-sm font-medium min-w-16 text-center"
               >{{ Math.round(zoomLevel * 100) }}%</span
            >
            <button @click="zoomIn" class="px-2 py-1 bg-gray-200 hover:bg-gray-300 text-sm rounded">
               +
            </button>
            <div class="w-px bg-gray-300" />
            <input v-model="drawColor" type="color" class="w-8 h-8 rounded" />
            <label class="flex items-center gap-2 text-sm">
               <input v-model.number="brushSize" type="range" min="1" max="40" class="w-24" />
               <span class="w-8 text-xs">{{ brushSize }}</span>
            </label>
            <label class="flex items-center gap-2 text-sm">
               <span>Opacity:</span>
               <input
                  v-model.number="brushAlpha"
                  type="range"
                  min="0.05"
                  max="1"
                  step="0.05"
                  class="w-24"
               />
               <span class="w-8 text-xs">{{ Math.round(brushAlpha * 100) }}%</span>
            </label>
         </div>
      </div>

      <!-- PDF Container with inline rendering -->
      <div class="flex-1 overflow-auto bg-gray-50 flex items-start py-4" @scroll="handleScroll">
         <div class="relative inline-block mx-auto">
            <!-- PDF pages rendered inline -->
            <div
               v-for="pageNum in totalPages"
               :key="`${pdfId}-${pageNum}`"
               class="relative mb-4 shadow-lg"
            >
               <canvas :id="`pdf-page-${pdfId}-${pageNum}`" class="block border border-gray-300" />
               <!-- Annotation overlay for this page -->
               <canvas
                  :id="`annotation-${pdfId}-${pageNum}`"
                  :class="['absolute top-0 left-0 border border-transparent', { drawing: true }]"
                  :style="{
                     cursor: 'none',
                  }"
                  @mousedown="handleDrawStart"
                  @mousemove="handleMouseMove"
                  @mouseenter="handleCursorEnter"
                  @mouseup="handleDrawEnd"
                  @mouseleave="handleCursorLeave"
               />
               <div
                  v-if="cursorVisible && cursorPage === pageNum"
                  class="absolute pointer-events-none rounded-full border border-white/70"
                  :style="{
                     left: `${cursorX - (brushSize * zoomLevel) / 2}px`,
                     top: `${cursorY - (brushSize * zoomLevel) / 2}px`,
                     width: `${brushSize * zoomLevel}px`,
                     height: `${brushSize * zoomLevel}px`,
                     backgroundColor: cursorColor,
                     boxShadow: '0 0 0 1px rgba(0,0,0,0.25) inset',
                  }"
               />
            </div>
         </div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { ref, onMounted, markRaw, nextTick, computed, watch } from 'vue';
import * as pdfjsLib from 'pdfjs-dist';
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

interface Props {
   pdfUrl: string;
   pdfFilename?: string;
}

interface Annotation {
   page: number;
   x1: number;
   y1: number;
   x2: number;
   y2: number;
   color: string;
   size: number;
   alpha: number;
   pageWidth: number;
   pageHeight: number;
}

const props = defineProps<Props>();

// Set up pdf.js worker from node_modules
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker;

// Extract unique ID from PDF URL (attachment ID)
const pdfId = computed(() => {
   const match = props.pdfUrl.match(/\/([a-f0-9-]+)\/download/);
   return match ? match[1] : props.pdfUrl;
});

const drawColor = ref('#ff0000');
const brushSize = ref(20);
const brushAlpha = ref(0.2);
const zoomLevel = ref(1);
const totalPages = ref(0);
const pdfDocument = ref<any>(null);
const cursorX = ref(0);
const cursorY = ref(0);
const cursorVisible = ref(false);
const cursorPage = ref<number | null>(null);
const isLoading = ref(false);
const renderTasks = new Map<number, any>();

let lastX = 0;
let lastY = 0;
let lastPageNum = 0;
let isMouseDown = false;
const annotations = ref<Annotation[]>([]);
const MIN_STROKE_DISTANCE = 0.75;
const ALPHA_COMPENSATION = 0.5;

const getAnnotationScale = (ann: Annotation, canvas: HTMLCanvasElement) => {
   const baseWidth = ann.pageWidth || canvas.width;
   const baseHeight = ann.pageHeight || canvas.height;
   return {
      scaleX: baseWidth ? canvas.width / baseWidth : 1,
      scaleY: baseHeight ? canvas.height / baseHeight : 1,
   };
};

// Helper to get canvas elements by ID
const getPageCanvas = (pageNum: number) => {
   return document.getElementById(`pdf-page-${pdfId.value}-${pageNum}`) as HTMLCanvasElement | null;
};

const getAnnotationCanvas = (pageNum: number) => {
   return document.getElementById(
      `annotation-${pdfId.value}-${pageNum}`
   ) as HTMLCanvasElement | null;
};

const hexToRgba = (hex: string, alpha: number) => {
   const normalized = hex.replace('#', '').trim();
   const value =
      normalized.length === 3
         ? normalized
              .split('')
              .map((c) => c + c)
              .join('')
         : normalized;
   const r = parseInt(value.slice(0, 2), 16) || 0;
   const g = parseInt(value.slice(2, 4), 16) || 0;
   const b = parseInt(value.slice(4, 6), 16) || 0;
   return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

const cursorColor = computed(() =>
   hexToRgba(drawColor.value, Math.min(1, brushAlpha.value * ALPHA_COMPENSATION))
);

const handleDrawStart = (e: MouseEvent) => {
   const canvas = e.target as HTMLCanvasElement;
   if (!canvas) return;

   // Extract page number from element ID (format: annotation-{pdfKey}-{pageNum})
   const pageNumStr = canvas.id.split('-').pop();
   const pageNum = parseInt(pageNumStr || '0', 10);
   if (isNaN(pageNum)) return;

   lastPageNum = pageNum;

   const rect = canvas.getBoundingClientRect();
   lastX = e.clientX - rect.left;
   lastY = e.clientY - rect.top;
   cursorX.value = lastX;
   cursorY.value = lastY;
   cursorVisible.value = true;
   cursorPage.value = pageNum;
   isMouseDown = true;
};

const handleMouseMove = (e: MouseEvent) => {
   const canvas = e.target as HTMLCanvasElement;
   if (!canvas) return;

   const rect = canvas.getBoundingClientRect();
   const x = e.clientX - rect.left;
   const y = e.clientY - rect.top;

   const pageNumStr = canvas.id.split('-').pop();
   const pageNum = parseInt(pageNumStr || '0', 10);
   if (!isNaN(pageNum)) {
      cursorX.value = x;
      cursorY.value = y;
      cursorVisible.value = true;
      cursorPage.value = pageNum;
   }

   if (!isMouseDown) return;

   const dx = x - lastX;
   const dy = y - lastY;
   if (dx * dx + dy * dy < MIN_STROKE_DISTANCE * MIN_STROKE_DISTANCE) return;

   drawLine(x, y, lastPageNum);
   lastX = x;
   lastY = y;
};

const handleDrawEnd = () => {
   isMouseDown = false;
};

const handleCursorEnter = (e: MouseEvent) => {
   const canvas = e.target as HTMLCanvasElement;
   if (!canvas) return;
   const pageNumStr = canvas.id.split('-').pop();
   const pageNum = parseInt(pageNumStr || '0', 10);
   if (isNaN(pageNum)) return;
   cursorVisible.value = true;
   cursorPage.value = pageNum;
};

const handleCursorLeave = () => {
   isMouseDown = false;
   cursorVisible.value = false;
   cursorPage.value = null;
};

const drawLine = (toX: number, toY: number, pageNum: number) => {
   const canvas = getAnnotationCanvas(pageNum);
   if (!canvas) return;

   if (toX === lastX && toY === lastY) return;

   const ctx = canvas.getContext('2d');
   if (!ctx) return;

   // Draw on annotation canvas
   const effectiveAlpha = Math.min(1, brushAlpha.value * ALPHA_COMPENSATION);
   ctx.globalAlpha = effectiveAlpha;
   ctx.strokeStyle = drawColor.value;
   ctx.lineWidth = brushSize.value * zoomLevel.value;
   ctx.lineCap = 'round';
   ctx.lineJoin = 'round';
   ctx.beginPath();
   ctx.moveTo(lastX, lastY);
   ctx.lineTo(toX, toY);
   ctx.stroke();
   ctx.globalAlpha = 1.0;

   // Store annotation
   const annotation: Annotation = {
      page: pageNum,
      x1: lastX,
      y1: lastY,
      x2: toX,
      y2: toY,
      color: drawColor.value,
      size: brushSize.value,
      alpha: effectiveAlpha,
      pageWidth: canvas.width,
      pageHeight: canvas.height,
   };
   annotations.value.push(annotation);
   saveAnnotations();
};

const redrawAnnotations = () => {
   // Clear and redraw all annotation canvases
   for (let p = 1; p <= totalPages.value; p++) {
      const canvas = getAnnotationCanvas(p);
      if (!canvas) continue;

      const ctx = canvas.getContext('2d');
      if (ctx) {
         ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
   }

   // Redraw all annotations
   annotations.value.forEach((ann) => {
      const canvas = getAnnotationCanvas(ann.page);
      if (!canvas) return;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const { scaleX, scaleY } = getAnnotationScale(ann, canvas);

      ctx.globalAlpha = ann.alpha ?? 0.6;
      ctx.strokeStyle = ann.color;
      ctx.lineWidth = ann.size * scaleX;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.beginPath();
      ctx.moveTo(ann.x1 * scaleX, ann.y1 * scaleY);
      ctx.lineTo(ann.x2 * scaleX, ann.y2 * scaleY);
      ctx.stroke();
      ctx.globalAlpha = 1.0;
   });
};

const saveAnnotations = () => {
   const key = `pdf-annotations-${props.pdfUrl}`;
   localStorage.setItem(key, JSON.stringify(annotations.value));
};

const loadAnnotations = () => {
   const key = `pdf-annotations-${props.pdfUrl}`;
   const saved = localStorage.getItem(key);
   if (saved) {
      try {
         annotations.value = JSON.parse(saved);
         console.log(`Loaded ${annotations.value.length} annotations`);

         // Set brush parameters from last annotation if exists
         if (annotations.value.length > 0) {
            const lastAnnotation = annotations.value[annotations.value.length - 1];
            if (lastAnnotation) {
               drawColor.value = lastAnnotation.color;
               brushSize.value = lastAnnotation.size;
               brushAlpha.value = lastAnnotation.alpha ?? 0.6;
            }
         }

         redrawAnnotations();
      } catch (e) {
         console.error('Failed to parse annotations:', e);
      }
   }
};

const clearAnnotations = () => {
   annotations.value = [];
   const key = `pdf-annotations-${props.pdfUrl}`;
   localStorage.removeItem(key);
   redrawAnnotations();
};

const zoomIn = () => {
   zoomLevel.value = Math.min(zoomLevel.value + 0.2, 4);
   rerenderAllPages();
};

const zoomOut = () => {
   zoomLevel.value = Math.max(zoomLevel.value - 0.2, 0.2);
   rerenderAllPages();
};

const rerenderAllPages = async () => {
   if (!pdfDocument.value) return;
   for (let i = 1; i <= totalPages.value; i++) {
      await renderPage(i);
   }
   // Redraw annotations after pages are re-rendered
   redrawAnnotations();
};

const renderPage = async (pageNum: number) => {
   if (!pdfDocument.value) {
      console.error('No PDF document loaded');
      return;
   }

   try {
      console.log(`Starting to render page ${pageNum} at zoom ${zoomLevel.value}`);
      const page = await pdfDocument.value.getPage(pageNum);

      // Get the page's natural rotation and correct it to 0
      const pageRotation = page.rotate || 0;
      const correctedRotation = (360 - pageRotation) % 360;

      const viewport = page.getViewport({ scale: zoomLevel.value, rotation: correctedRotation });

      // Render to main canvas
      const canvas = getPageCanvas(pageNum);
      if (!canvas) {
         console.error(`Canvas for page ${pageNum} not found in DOM`);
         return;
      }

      console.log(`Setting canvas size to ${viewport.width}x${viewport.height}`);
      canvas.width = viewport.width;
      canvas.height = viewport.height;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
         console.error('Failed to get 2d context');
         return;
      }

      console.log(`Rendering page ${pageNum} at ${viewport.width}x${viewport.height}`);

      // Cancel any existing render task for this page
      if (renderTasks.has(pageNum)) {
         try {
            renderTasks.get(pageNum).cancel();
         } catch (e) {
            // Ignore cancellation errors
         }
      }

      // Test: fill canvas with light gray to verify it's visible
      ctx.fillStyle = '#f0f0f0';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const renderTask = page.render({
         canvasContext: ctx,
         viewport: viewport,
      });

      renderTasks.set(pageNum, renderTask);
      await renderTask.promise;
      renderTasks.delete(pageNum);

      // Set up annotation canvas with same dimensions
      const annCanvas = getAnnotationCanvas(pageNum);
      if (annCanvas) {
         annCanvas.width = viewport.width;
         annCanvas.height = viewport.height;

         // Make annotation canvas explicitly transparent
         const annCtx = annCanvas.getContext('2d');
         if (annCtx) {
            annCtx.clearRect(0, 0, annCanvas.width, annCanvas.height);
         }
      }

      console.log(
         `Page ${pageNum} rendered successfully - canvas dimensions: ${canvas.width}x${canvas.height}`
      );
   } catch (e) {
      console.error(`Failed to render page ${pageNum}:`, e);
   }
};

const handleScroll = () => {
   // Could add lazy loading here if needed for large PDFs
};

const loadPdf = async () => {
   if (isLoading.value) {
      console.log('PDF load already in progress, skipping...');
      return;
   }

   isLoading.value = true;
   try {
      // Cancel all pending render tasks
      for (const [, task] of renderTasks.entries()) {
         try {
            task.cancel();
         } catch (e) {
            // Ignore
         }
      }
      renderTasks.clear();

      // Cleanup previous PDF document
      if (pdfDocument.value) {
         try {
            await pdfDocument.value.destroy();
         } catch (e) {
            console.warn('Error destroying previous PDF:', e);
         }
      }

      // Clear previous state
      totalPages.value = 0;
      pdfDocument.value = null;

      // Wait for DOM to clear old canvases
      await nextTick();
      await new Promise((resolve) => setTimeout(resolve, 50));

      // Fetch PDF data first to handle CORS/auth properly
      const response = await fetch(props.pdfUrl);

      if (!response.ok) {
         throw new Error(`Failed to fetch PDF: ${response.status} ${response.statusText}`);
      }

      const blob = await response.blob();
      const arrayBuffer = await blob.arrayBuffer();

      // Load PDF from array buffer - use markRaw to prevent Vue reactivity from breaking pdfjs
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      pdfDocument.value = markRaw(pdf);
      totalPages.value = pdf.numPages;

      console.log(`Loaded PDF with ${pdf.numPages} pages from URL: ${props.pdfUrl}`);

      // Wait for DOM to update with the canvas elements
      await nextTick();

      // Wait a bit more for canvas elements to be fully mounted
      await new Promise((resolve) => setTimeout(resolve, 100));

      // Debug: check if canvas elements exist
      console.log(`Total pages ref: ${totalPages.value}, pdfId: ${pdfId.value}`);
      for (let i = 1; i <= pdf.numPages; i++) {
         const canvas = document.getElementById(`pdf-page-${pdfId.value}-${i}`);
         console.log(`Canvas pdf-page-${pdfId.value}-${i} exists:`, !!canvas);
      }

      // Render all pages
      for (let i = 1; i <= pdf.numPages; i++) {
         await renderPage(i);
      }

      loadAnnotations();
   } catch (e) {
      console.error('Failed to load PDF:', e);
   } finally {
      isLoading.value = false;
   }
};

onMounted(() => {
   console.log('PdfAnnotator mounted');
   loadPdf();
});

watch(
   () => props.pdfUrl,
   (newUrl, oldUrl) => {
      if (newUrl !== oldUrl) {
         console.log(`PDF URL changed from ${oldUrl} to ${newUrl}, reloading...`);
         annotations.value = [];
         loadPdf();
      }
   }
);
</script>

<style scoped>
canvas {
   display: block;
   width: auto;
   height: auto;
   touch-action: none;
}

canvas.block {
   background-color: white;
}

canvas.absolute {
   background-color: transparent !important;
   pointer-events: none;
}

canvas.absolute.drawing {
   pointer-events: auto;
}

div[class*='inline-block'] {
   margin: 0 auto;
}
</style>
