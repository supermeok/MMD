<template>
  <div class="flow-zone">
    <div class="flow-branch left" :class="{ active: leftActive }"></div>
    <div class="flow-branch middle" :class="{ active: middleActive }"></div>
    <div class="flow-branch right" :class="{ active: rightActive }"></div>

    <div class="flow-hub-line" :class="{ active: mergeActive }"></div>
    <div class="flow-node" :class="{ active: mergeActive }"></div>
    <div class="flow-drop-line" :class="{ active: mergeActive }"></div>
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