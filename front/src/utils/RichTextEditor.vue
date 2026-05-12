<template>
   <textarea
      ref="textareaRef"
      :value="modelValue"
      v-bind="$attrs"
      class="overflow-hidden resize-none"
      @input="handleInput"
      @blur="handleBlur"
      @keydown="handleKeydown"
   />
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue';

defineOptions({
   inheritAttrs: false,
});

const props = defineProps<{
   modelValue: string;
}>();

const emit = defineEmits<{
   (e: 'update:modelValue', value: string): void;
   (e: 'input', event: Event): void;
   (e: 'blur', event: FocusEvent): void;
   (e: 'keydown', event: KeyboardEvent): void;
}>();

const textareaRef = ref<HTMLTextAreaElement | null>(null);
const pendingScroll = ref<{
   pageY: number;
   scrollTop: number;
} | null>(null);

const resizeTextarea = () => {
   const el = textareaRef.value;
   if (!el) return;
   el.style.height = 'auto';
   el.style.height = `${el.scrollHeight}px`;
};

const handleInput = (event: Event) => {
   const target = event.target as HTMLTextAreaElement;
   const snapshot = pendingScroll.value ?? {
      pageY: window.scrollY,
      scrollTop: target.scrollTop,
   };

   emit('update:modelValue', target.value);
   emit('input', event);

   nextTick(() => {
      resizeTextarea();
      if (document.activeElement === target) {
         target.scrollTop = snapshot.scrollTop;
      }
      requestAnimationFrame(() => {
         if (window.scrollY !== snapshot.pageY) {
            window.scrollTo({ top: snapshot.pageY });
         }
         requestAnimationFrame(() => {
            if (window.scrollY !== snapshot.pageY) {
               window.scrollTo({ top: snapshot.pageY });
            }
         });
      });
      pendingScroll.value = null;
   });
};

const handleBlur = (event: FocusEvent) => {
   emit('blur', event);
};

const handleKeydown = (event: KeyboardEvent) => {
   const target = event.target as HTMLTextAreaElement | null;
   if (target) {
      pendingScroll.value = {
         pageY: window.scrollY,
         scrollTop: target.scrollTop,
      };
   }
   emit('keydown', event);
};

const getTextarea = () => textareaRef.value;
const focus = () => textareaRef.value?.focus();

onMounted(() => {
   nextTick(() => resizeTextarea());
});

watch(
   () => props.modelValue,
   () => {
      nextTick(() => resizeTextarea());
   }
);

defineExpose({ getTextarea, focus, resizeTextarea });
</script>
