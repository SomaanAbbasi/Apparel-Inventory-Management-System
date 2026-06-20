// Preloader/transition script
document.addEventListener("DOMContentLoaded", () => {
  // Get the preloader and content elements
  const preloader = document.querySelector(".preloader")
  const contentWrapper = document.querySelector(".content-wrapper")

  // Function to handle the page load transition
  function handlePageLoad() {
    // Add the fade-out class to the preloader
    preloader.classList.add("fade-out")

    // Add the loaded class to the content wrapper
    setTimeout(() => {
      contentWrapper.classList.add("loaded")
    }, 200)

    // Remove the preloader from the DOM after the transition
    setTimeout(() => {
      preloader.style.display = "none"
    }, 800)
  }

  // If the page is already loaded, handle the transition immediately
  if (document.readyState === "complete") {
    handlePageLoad()
  } else {
    // Otherwise, wait for the window load event
    window.addEventListener("load", handlePageLoad)
  }
})