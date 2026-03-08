<template>
  <div class="flow-zone">
    <div class="flow-line left" :class="{ active: leftActive }"></div>
    <div class="flow-line middle" :class="{ active: middleActive }"></div>
    <div class="flow-line right" :class="{ active: rightActive }"></div>
    <div class="merge-line" :class="{ active: mergeActive }"></div>
    <div class="flow-core" :class="{ active: mergeActive }"></div>
  </div>
</template>

<script setup>
defineProps({
  leftActive: Boolean,
  middleActive: Boolean,
  rightActive: Boolean,
  mergeActive: Boolean
})
</script>