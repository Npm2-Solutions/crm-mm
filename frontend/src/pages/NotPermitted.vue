<template>
  <div
    class="flex flex-col items-center justify-center min-h-screen bg-surface-gray-1"
  >
    <div class="w-full max-w-md px-6 text-center">
      <h1 class="text-ink-gray-8 text-4xl-semibold">
        {{ __('Access Denied') }}
      </h1>
      <div class="border-t border-outline-gray-2 w-full my-[15px]" />
      <p class="text-ink-gray-6 text-p-base">
        {{
          __(
            'You do not have enough permissions to access DottorCloud. Please contact your administrator if you believe this is an error.',
          )
        }}
      </p>

      <Button
        class="mt-5 w-full"
        variant="solid"
        :label="__('Login with Different Account')"
        @click="logout.submit()"
      />
    </div>
  </div>
</template>
<script setup>
import { sessionStore } from '@/stores/session'
const { logout } = sessionStore()
</script>
