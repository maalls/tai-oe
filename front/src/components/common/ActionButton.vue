<template>
   <button :type="type" :disabled="disabled" :class="buttonClass">
      <slot />
   </button>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
   type: {
      type: String,
      default: 'button',
   },
   variant: {
      type: String,
      default: 'primary',
   },
   disabled: {
      type: Boolean,
      default: false,
   },
});

const variantClassMap = {
   primary: 'bg-blue-600 text-white hover:bg-blue-700',
   danger: 'bg-red-600 text-white hover:bg-red-700',
   neutral: 'bg-gray-300 text-gray-800 hover:bg-gray-400',
};

const buttonClass = computed(() => {
   const variantClass = variantClassMap[props.variant] || variantClassMap.primary;
   return [
      'inline-flex h-8 items-center justify-center px-2 text-sm rounded transition cursor-pointer',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      variantClass,
   ];
});
</script>
