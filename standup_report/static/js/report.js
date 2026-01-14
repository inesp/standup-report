const showIgnoreBtns = document.getElementById("show-ignore-btns");
const showTimestamps = document.getElementById("show-timestamps");
const showCreated = document.getElementById("show-created");
const slackFormat = document.getElementById("slack-format");

showIgnoreBtns.addEventListener("change", () => {
  document.querySelectorAll(".ignore-btn").forEach((el) => {
    el.classList.toggle("hidden", !showIgnoreBtns.checked);
  });
});

showTimestamps.addEventListener("change", () => {
  document.querySelectorAll(".last-change-ago").forEach((el) => {
    el.classList.toggle("hidden", !showTimestamps.checked);
  });
});

showCreated.addEventListener("change", () => {
  document
    .querySelectorAll(".activity-item.item-created-issue")
    .forEach((el) => {
      el.classList.toggle("hidden", !showCreated.checked);
    });
});

slackFormat.addEventListener("change", () => {
  document.querySelectorAll(".original-link").forEach((el) => {
    el.classList.toggle("hidden", slackFormat.checked);
  });
  document.querySelectorAll(".slack-link").forEach((el) => {
    el.classList.toggle("hidden", !slackFormat.checked);
  });
});

// Reusable function to show messages
function showMessage(message, type = "error") {
  const el = document.querySelector(".error-placeholder");
  const styles =
    type === "error"
      ? "bg-red-100 border-red-400 text-red-700"
      : "bg-green-100 border-green-400 text-green-700";
  el.innerHTML = `
    <div class="${styles} border px-4 py-3 rounded mb-4">
      ${message}
    </div>
  `;
  setTimeout(() => {
    el.innerHTML = "";
  }, 5000);
}

// Add item to ignored list
function addToIgnoredList(itemType, itemId, itemTitle) {
  const section = document.getElementById("ignored-section");
  const list = document.getElementById("ignored-list");

  section.classList.remove("hidden");

  const p = document.createElement("p");
  p.className = "mb-1";
  p.innerHTML = `
    <button class="unignore-btn mr-4 text-red-500 hover:text-red-500 font-bold text-lg"
      data-item-type="${itemType}"
      data-item-id="${itemId}"
      title="Unignore"
    >➕</button> ${itemType} ${itemId} ${itemTitle}
  `;

  p.querySelector(".unignore-btn").addEventListener("click", (e) =>
    handleIgnoreClick(e, "unignore"),
  );
  list.appendChild(p);
}

// Reusable handler for both ignore and unignore
async function handleIgnoreClick(e, action) {
  const btn = e.target;
  const itemType = btn.dataset.itemType;
  const itemId = btn.dataset.itemId;
  const itemTitle = btn.dataset.itemTitle;
  const itemRow = btn.closest("p");

  let url = `/api/${action}/${itemType}/${itemId}`;
  if (action === "ignore" && itemTitle) {
    url += `?title=${encodeURIComponent(itemTitle)}`;
  }

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (response.ok) {
      itemRow.remove();
      if (action === "ignore") {
        addToIgnoredList(itemType, itemId, itemTitle);
      } else {
        showMessage(
          "Item unignored. Reload to see it in Done/Next. (We have to fetch all of its data again from the remote.)",
          "info",
        );
      }
    } else {
      const data = await response.json();
      showMessage(data.error);
    }
  } catch (error) {
    showMessage("Network error, please try again");
  }
}

// Attach to both button types
document.querySelectorAll(".ignore-btn").forEach((btn) => {
  btn.addEventListener("click", (e) => handleIgnoreClick(e, "ignore"));
});

document.querySelectorAll(".unignore-btn").forEach((btn) => {
  btn.addEventListener("click", (e) => handleIgnoreClick(e, "unignore"));
});
