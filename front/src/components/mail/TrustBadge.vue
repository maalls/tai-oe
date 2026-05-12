<template>
   <div class="inline-flex items-center gap-2">
      <!-- Trust Badge Icon -->
      <div
         :class="['inline-flex items-center justify-center w-6 h-6 rounded-full', badgeClasses]"
         :title="tooltipText"
      >
         <svg
            v-if="trustLevel === 'verified'"
            class="w-4 h-4"
            fill="currentColor"
            viewBox="0 0 20 20"
         >
            <path
               fill-rule="evenodd"
               d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 3.062v6.757a3.066 3.066 0 01-3.062 3.062H7.065a3.066 3.066 0 01-3.062-3.062V6.517a3.066 3.066 0 012.812-3.062zm7.069 4.175a.75.75 0 00-1.06-1.06l-5.75 5.75-2.437-2.437a.75.75 0 00-1.06 1.06l3.5 3.5a.75.75 0 001.06 0l6.25-6.25z"
               clip-rule="evenodd"
            />
         </svg>
         <svg
            v-else-if="trustLevel === 'partial'"
            class="w-4 h-4"
            fill="currentColor"
            viewBox="0 0 20 20"
         >
            <path
               d="M8.485 2.495c.674-1.346 2.356-1.346 3.03 0l2.894 5.79 6.39.464c1.794.13 2.513 2.148 1.123 3.305L15.873 13.16l1.764 6.443c.372 1.361-.64 2.487-1.877 2.15L10 15.347l-5.76 1.406c-1.237.337-2.249-.789-1.877-2.15l1.764-6.443L1.166 11.854c-1.39-1.157-.67-3.174 1.123-3.305l6.39-.464 2.894-5.79z"
            />
         </svg>
         <svg
            v-else-if="trustLevel === 'unverified'"
            class="w-4 h-4"
            fill="currentColor"
            viewBox="0 0 20 20"
         >
            <path
               fill-rule="evenodd"
               d="M8.485 2.495c.674-1.346 2.356-1.346 3.03 0l2.894 5.79 6.39.464c1.794.13 2.513 2.148 1.123 3.305L15.873 13.16l1.764 6.443c.372 1.361-.64 2.487-1.877 2.15L10 15.347l-5.76 1.406c-1.237.337-2.249-.789-1.877-2.15l1.764-6.443L1.166 11.854c-1.39-1.157-.67-3.174 1.123-3.305l6.39-.464 2.894-5.79z"
               opacity="0.4"
            />
         </svg>
      </div>

      <!-- Trust Score Display -->
      <div v-if="showScore" class="text-xs font-semibold" :class="scoreTextClasses">
         {{ authScore }}%
      </div>

      <!-- Verification Status Dot -->
      <div v-if="showDot" class="flex items-center gap-1">
         <div :class="['w-2 h-2 rounded-full', isVerified ? 'bg-green-500' : 'bg-red-500']"></div>
      </div>
   </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
   authScore?: number;
   isVerified?: boolean;
   spfStatus?: string;
   dkimStatus?: string;
   dmarcStatus?: string;
   showScore?: boolean;
   showDot?: boolean;
   size?: 'sm' | 'md' | 'lg';
}

const props = withDefaults(defineProps<Props>(), {
   authScore: 0,
   isVerified: false,
   showScore: true,
   showDot: false,
   size: 'md',
});

// Determine trust level based on score and verification
const trustLevel = computed(() => {
   if (props.isVerified && props.authScore >= 80) {
      return 'verified';
   } else if (props.authScore >= 50) {
      return 'partial';
   }
   return 'unverified';
});

// Badge styling based on trust level
const badgeClasses = computed(() => {
   switch (trustLevel.value) {
      case 'verified':
         return 'bg-green-100 text-green-700';
      case 'partial':
         return 'bg-yellow-100 text-yellow-700';
      case 'unverified':
      default:
         return 'bg-red-100 text-red-700';
   }
});

// Score text color
const scoreTextClasses = computed(() => {
   switch (trustLevel.value) {
      case 'verified':
         return 'text-green-700';
      case 'partial':
         return 'text-yellow-700';
      case 'unverified':
      default:
         return 'text-red-700';
   }
});

// Tooltip text with details
const tooltipText = computed(() => {
   const details = [];

   if (props.spfStatus) {
      details.push(`SPF: ${props.spfStatus}`);
   }
   if (props.dkimStatus) {
      details.push(`DKIM: ${props.dkimStatus}`);
   }
   if (props.dmarcStatus) {
      details.push(`DMARC: ${props.dmarcStatus}`);
   }

   const statusLine = props.isVerified ? '✓ Verified sender' : '⚠ Unverified sender';

   if (details.length > 0) {
      return `${statusLine}\n${details.join('\n')}`;
   }

   return statusLine;
});
</script>
