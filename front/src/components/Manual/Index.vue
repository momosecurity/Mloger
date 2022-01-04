<template>
  <div class="layout">
    <div style="padding: 15px" class="markdown-body">
      <markdown></markdown>
    </div>
  </div>
</template>

<script>
import markdown from '@/assets/usage.md'
import 'github-markdown-css'

export default {
  components: {
    markdown
  },
  name: "ManualIndex"
}
</script>

<style scoped>
.markdown-body {
  box-sizing: border-box;
  min-width: 200px;
  max-width: 980px;
  margin: 0 auto;
  padding: 45px;
}
</style>