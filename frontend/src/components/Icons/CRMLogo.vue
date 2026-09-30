<!--
  The app's icon: DottorCloud's mark - a cloud with a cross cut out of it - white
  on the teal square (brand/logo/dottorcloud-icona-app.svg). Where a centre has
  uploaded its own logo, BrandLogo shows that one instead.
-->
<template>
  <svg
    viewBox="0 0 512 512"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    role="img"
    aria-label="DottorCloud"
  >
    <defs>
      <!-- an id per icon: two on the same page must not share a gradient -->
      <linearGradient :id="sfumatura" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#17b8a4" />
        <stop offset="1" stop-color="#0b6f64" />
      </linearGradient>
    </defs>
    <rect width="512" height="512" rx="112" :fill="`url(#${sfumatura})`" />
    <path
      transform="translate(103.02 122.88) scale(3.4595) translate(-12 -14)"
      d="M12 40C12 25.64 23.64 14 38 14C49.74 14 59.66 21.78 62.89 32.46C64.55 32.16 66.26 32 68 32C83.46 32 96 44.54 96 60C96 75.46 83.46 88 68 88H24C17.37 88 12 82.63 12 76ZM50.5 45C48.57 45 47 46.57 47 48.5V55H40.5C38.57 55 37 56.57 37 58.5V63.5C37 65.43 38.57 67 40.5 67H47V73.5C47 75.43 48.57 77 50.5 77H55.5C57.43 77 59 75.43 59 73.5V67H65.5C67.43 67 69 65.43 69 63.5V58.5C69 56.57 67.43 55 65.5 55H59V48.5C59 46.57 57.43 45 55.5 45Z"
      fill="#ffffff"
    />
  </svg>
</template>

<script setup>
import { useId } from 'vue'

const sfumatura = `dc-${useId()}`
</script>
