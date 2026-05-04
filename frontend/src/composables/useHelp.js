import { ref } from 'vue'

const isOpen = ref(false)
const currentTitle = ref('')
const currentContent = ref('')

export function useHelp() {
  const openHelp = (title, content) => {
    currentTitle.value = title
    currentContent.value = content
    isOpen.value = true
  }

  const closeHelp = () => {
    isOpen.value = false
  }

  return {
    isOpen,
    currentTitle,
    currentContent,
    openHelp,
    closeHelp
  }
}
