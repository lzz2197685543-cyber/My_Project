<template>
  <div id="app">
    <ChatInterface />
  </div>
</template>
<script setup>
import ChatInterface from './components/ChatInterface.vue'
</script>
<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  background: #f5f7fa;
  color: #2c3e50;
}

#app {
  height: 100vh;
}
</style>
