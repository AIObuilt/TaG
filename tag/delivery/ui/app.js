document.querySelectorAll("[data-runtime]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelector("#governance-state").textContent =
      `Runtime path selected: ${button.dataset.runtime}`;
  });
});
