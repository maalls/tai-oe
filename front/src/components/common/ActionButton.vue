<template>
   <component :is="componentTag" v-bind="componentAttrs" :class="buttonClass">
      <slot />
   </component>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
   to: {
      type: [String, Object],
      default: null,
   },
   type: {
      type: String,
      default: 'button',
   },
   variant: {
      type: String,
      default: 'primary',
   },
   size: {
      type: String,
      default: 'sm',
   },
   disabled: {
      type: Boolean,
      default: false,
   },
});

const variantClassMap = {
   primary: 'bg-blue-600 text-white hover:bg-blue-700',
   danger: 'bg-red-600 text-white hover:bg-red-700',
   'danger-outline': 'bg-white border border-red-200 text-red-600 hover:bg-red-50',
   neutral: 'bg-gray-300 text-gray-800 hover:bg-gray-400',
   dark: 'bg-gray-600 text-white hover:bg-gray-700',
};

const sizeClassMap = {
   sm: 'h-8 px-2 text-sm',
   xs: 'h-7 px-2 text-xs',
};

const componentTag = computed(() => (props.to ? 'router-link' : 'button'));

const componentAttrs = computed(() => {
   if (props.to) {
      return { to: props.to };
   }

   return {
      type: props.type,
      disabled: props.disabled,
   };
});

const buttonClass = computed(() => {
   const variantClass = variantClassMap[props.variant] || variantClassMap.primary;
   const sizeClass = sizeClassMap[props.size] || sizeClassMap.sm;
   return [
      'inline-flex items-center justify-center rounded transition cursor-pointer',
      sizeClass,
      'disabled:opacity-50 disabled:cursor-not-allowed',
      variantClass,
   ];
});
</script>
