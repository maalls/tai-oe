# PDF Annotation Positioning - Debug & Fix Summary

## Changes Made (Session 2)

### 1. Fixed Critical Drawing Bugs

**File**: `PdfAnnotator.vue`

**Issue**: The `drawLine()` function had two bugs:

- Missing `ctx.stroke()` call after drawing line segments
- Only updating `lastY` instead of both `lastX` and `lastY` for the next segment

**Fix**:

```typescript
ctx.beginPath();
ctx.moveTo(lastX, lastY);
ctx.lineTo(toX, toY);
ctx.stroke(); // ← WAS MISSING
lastX = toX; // ← WAS MISSING
lastY = toY; // ← WAS ONLY DOING THIS
```

**Impact**: Lines now render correctly and chain together properly

### 2. Added Coordinate Clamping

**File**: `PdfAnnotator.vue` - `handleDrawMove()`

**Issue**: Mouse coordinates could exceed canvas boundaries causing visual glitches

**Fix**: Clamp coordinates to [0, canvas.width] and [0, canvas.height] before drawing

```typescript
const clampedX = Math.max(0, Math.min(x, canvas.width));
const clampedY = Math.max(0, Math.min(y, canvas.height));
drawLine(clampedX, clampedY);
```

### 3. Removed Unreliable Cross-Origin Offset Detection

**File**: `PdfAnnotator.vue`

**Issue**: Attempted to detect PDF viewer offset by querying iframe DOM, but:

- Cross-origin restrictions block access to `iframe.contentDocument`
- Even with CORS headers, couldn't access PDF viewer's internal positioning
- The detectPdfOffset() function was providing unreliable data

**Fix**:

- Removed `pdfOffsetX` and `pdfOffsetY` refs (lines 151-152)
- Deleted entire `detectPdfOffset()` function (36 lines)
- Removed all calls to `detectPdfOffset()` from PDF load and resize handlers

**Rationale**: Can't reliably access cross-origin iframe content, so offset tracking won't work

### 4. Integrated PDFjs for PDF Metadata

**File**: `PdfAnnotator.vue`

**Changes**:

```typescript
import * as PDFJS from 'pdfjs-dist';
PDFJS.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${PDFJS.version}/pdf.worker.min.js`;

const pdfPageWidth = ref(0);
const pdfPageHeight = ref(0);

const loadPdfDimensions = async (pdfUrl: string) => {
   try {
      const pdf = await PDFJS.getDocument(pdfUrl).promise;
      const page = await pdf.getPage(1);
      const viewport = page.getViewport({ scale: 1.0 });
      pdfPageWidth.value = viewport.width;
      pdfPageHeight.value = viewport.height;
   } catch (e) {
      addDebugLog(`Cannot load PDF dimensions: ${e}`);
   }
};
```

**Purpose**: Store actual PDF page dimensions (e.g., 612x792 for standard letter) to have reference coordinates

**Updated onMounted**: Added `loadPdfDimensions(props.pdfUrl)` call

### 5. Extended LineSegment Interface

**File**: `PdfAnnotator.vue`

**Before**:

```typescript
interface LineSegment {
   fromX: number;
   fromY: number;
   toX: number;
   toY: number;
   color: string;
   size: number;
   alpha: number;
   normalized?: boolean;
}
```

**After**:

```typescript
interface LineSegment {
   fromX: number;
   fromY: number;
   toX: number;
   toY: number;
   color: string;
   size: number;
   alpha: number;
   normalized?: boolean;
   storedCanvasWidth?: number; // ← NEW
   storedCanvasHeight?: number; // ← NEW
   pdfPageWidth?: number; // ← NEW
   pdfPageHeight?: number; // ← NEW
}
```

**Purpose**: Store metadata about dimensions when annotation was created, helps with resize handling and PDF-relative positioning

### 6. Enhanced drawLine() to Store Dimensions

**File**: `PdfAnnotator.vue`

**Updated**:

```typescript
const segment: LineSegment = {
   fromX: normalizedFromX,
   fromY: normalizedFromY,
   toX: normalizedToX,
   toY: normalizedToY,
   color: drawColor.value,
   size: brushSize.value,
   alpha: drawAlpha.value,
   normalized: true,
   storedCanvasWidth: safeWidth, // ← NEW
   storedCanvasHeight: safeHeight, // ← NEW
   pdfPageWidth: pdfPageWidth.value, // ← NEW
   pdfPageHeight: pdfPageHeight.value, // ← NEW
};
```

### 7. Enhanced Debugging

**File**: `PdfAnnotator.vue`

**Added logging to key functions**:

**drawLine()**:

```typescript
console.log(`Draw: canvas=${safeWidth}x${safeHeight}, 
            pixel=(${lastX},${lastY})->(${toX},${toY}), 
            normalized=(${normalizedFromX.toFixed(4)},...)`);
```

**handleDrawStart()**:

```typescript
const iframeRect = iframe.getBoundingClientRect();
const canvasRect = canvas.getBoundingClientRect();
console.log(`Draw start - Canvas at (${canvasRect.left},...), Iframe at (${iframeRect.left},...)`);
```

**handleWindowResize()**:

```typescript
console.log(`Resize - Canvas: ${canvasRect.width}x${canvasRect.height} at (...) | 
            Iframe: ${iframeRect.width}x${iframeRect.height} at (...)`);
```

**Purpose**: Track exact bounding rectangles and coordinate transformations to identify where positioning breaks

### 8. CSS Fixes for iframe

**File**: `PdfAnnotator.vue`

**Added styles**:

```css
iframe {
   overflow: hidden !important; /* Prevent scrollbars that might shift content */
   zoom: 1; /* Prevent browser zoom artifacts */
}
```

**Rationale**:

- Scrollbars can appear/disappear causing layout shifts
- Browser zoom can affect coordinate calculations
- `zoom=page-width` URL param already set, CSS ensures no additional zoom

## Current State

### Working Features ✓

- Drawings render correctly with proper line continuity
- Normalized coordinate storage for resize robustness
- localStorage persistence
- PDF dimensions now tracked
- Extensive logging for debugging
- Coordinates clamped to canvas bounds

### Known Issues 🔴

- **Positioning still shifts on resize** - Root cause still unknown, awaiting debug logs
- Cannot reliably detect PDF viewer offset due to cross-origin restrictions
- PDF viewer internal repositioning on resize not fully understood

## Next Steps

### Phase 1: Test & Diagnose (Ready)

1. Start dev server
2. Load a PDF in SourceViewer
3. Draw annotation in PdfAnnotator
4. Open browser console (F12)
5. Resize window and observe:
   - Canvas dimensions before/after
   - Iframe bounding rect before/after
   - Annotation expected vs actual positions
6. Log analysis to identify root cause

### Phase 2: Implement Fix (Depends on Phase 1)

**If Canvas/Iframe both scale correctly but still misaligned**:

- Root cause: PDF viewer repositioning content independently
- Solution: Lock PDF zoom level and prevent responsive scaling

**If Iframe position shifts relative to container**:

- Root cause: Container layout changes affecting iframe position
- Solution: Use position offsets in coordinate calculations

**If PDF margins/centering changes on resize**:

- Root cause: PDF viewer centers PDFs differently based on width
- Solution: Either accept it, or use fixed-size container

## Testing Checklist

After changes are tested and verified:

- [ ] Draw single line segment, verify renders
- [ ] Draw multiple connected segments, verify continuity
- [ ] Resize window smaller, check annotation position
- [ ] Resize window larger, check annotation position
- [ ] Reload page, verify annotations persist
- [ ] Check browser console for errors
- [ ] Verify no JavaScript syntax errors
- [ ] Test with different PDF sizes
- [ ] Test with different viewport sizes

## Files Modified

1. `front/src/components/PdfAnnotator.vue` - All changes above
2. `front/PDF_ANNOTATION_FIX.md` - Problem analysis (new file)

## Rollback

If issues arise, revert with:

```bash
git checkout front/src/components/PdfAnnotator.vue
```

The key commit points are:

1. Fixed drawing bugs
2. Removed offset detection
3. Added PDF metadata tracking
4. Enhanced logging
