const showIgnoreBtns = document.getElementById("show-ignore-btns");
const showTimestamps = document.getElementById("show-timestamps");
const showCreated = document.getElementById("show-created");
const showMeetings = document.getElementById("show-meetings");
const slackFormat = document.getElementById("slack-format");
const showNoteInputs = document.getElementById("show-note-inputs");
const showMeetingTimes = document.getElementById("show-meeting-times");

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

showMeetingTimes.addEventListener("change", () => {
  document.querySelectorAll(".meeting-time").forEach((el) => {
    el.classList.toggle("hidden", !showMeetingTimes.checked);
  });
});

showCreated.addEventListener("change", () => {
  document
    .querySelectorAll(".activity-item.item-created-issue")
    .forEach((el) => {
      el.classList.toggle("hidden", !showCreated.checked);
    });
});

showMeetings.addEventListener("change", () => {
  document.querySelectorAll(".activity-item.item-meeting").forEach((el) => {
    el.classList.toggle("hidden", !showMeetings.checked);
  });
});

slackFormat.addEventListener("change", () => {
  document.querySelectorAll(".original-link").forEach((el) => {
    el.classList.toggle("hidden", slackFormat.checked);
  });
  document.querySelectorAll(".slack-link").forEach((el) => {
    el.classList.toggle("hidden", !slackFormat.checked);
  });

  // Disable note editing when slack format is on
  if (slackFormat.checked) {
    showNoteInputs.checked = false;
  }
  showNoteInputs.dispatchEvent(new Event("change"));
});

showNoteInputs.addEventListener("change", () => {
  const isEditing = showNoteInputs.checked;

  // Toggle inputs: show when editing, hide when readonly (except empty ones always use input)
  document.querySelectorAll(".note-input").forEach((el) => {
    const isEmpty = el.classList.contains("note-empty");
    if (isEmpty) {
      // Empty inputs: show only when editing
      el.classList.toggle("hidden", !isEditing);
    } else {
      // Inputs with content: show when editing, hide when readonly
      el.classList.toggle("hidden", !isEditing);
    }
  });

  // Toggle display spans: show when readonly, hide when editing
  document.querySelectorAll(".note-display").forEach((el) => {
    el.classList.toggle("hidden", isEditing);
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

// Handle note input changes
async function saveNote(input) {
  const itemType = input.dataset.itemType;
  const itemId = input.dataset.itemId;
  const category = input.dataset.category;
  const note = input.value.trim();

  const url = `/api/note/${itemType}/${itemId}/${category}`;

  // Show loading state
  input.classList.add("note-saving");
  input.disabled = true;
  const startTime = Date.now();
  const minDuration = 500;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note }),
    });

    if (!response.ok) {
      const data = await response.json();
      showMessage(data.error);
    } else {
      const parent = input.closest(".activity-item");
      let span = parent.querySelector(".note-display");

      if (note) {
        input.classList.remove("note-empty");
        // Create or update span
        if (!span) {
          span = document.createElement("span");
          span.className = "note-display";
          input.insertAdjacentElement("beforebegin", span);
        }
        span.textContent = note;
        // Show/hide based on editing mode
        span.classList.toggle("hidden", showNoteInputs.checked);
        input.classList.toggle("hidden", !showNoteInputs.checked);
      } else {
        input.classList.add("note-empty");
        // Remove span if exists
        if (span) {
          span.remove();
        }
        // Hide input if not editing
        if (!showNoteInputs.checked) {
          input.classList.add("hidden");
        }
      }
      // Update title for tooltip
      input.title = note;
    }
  } catch (error) {
    showMessage("Network error saving note");
  } finally {
    // Remove loading state after minimum duration
    const elapsed = Date.now() - startTime;
    const remaining = Math.max(0, minDuration - elapsed);
    setTimeout(() => {
      input.classList.remove("note-saving");
      input.disabled = false;
    }, remaining);
  }
}

document.querySelectorAll(".note-input").forEach((input) => {
  input.addEventListener("blur", () => saveNote(input));
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      input.blur();
    }
  });
});

// Clear all notes button
const clearAllNotesBtn = document.getElementById("clear-all-notes-btn");
if (clearAllNotesBtn) {
  clearAllNotesBtn.addEventListener("click", async () => {
    if (
      !confirm(
        "Are you sure you want to delete all notes? This cannot be undone.",
      )
    ) {
      return;
    }

    clearAllNotesBtn.disabled = true;
    clearAllNotesBtn.textContent = "Deleting...";

    try {
      const response = await fetch("/api/notes/delete-all", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (response.ok) {
        const data = await response.json();
        // Clear all note inputs and displays
        document.querySelectorAll(".note-input").forEach((input) => {
          input.value = "";
          input.classList.add("note-empty");
        });
        document.querySelectorAll(".note-display").forEach((span) => {
          span.innerHTML = "";
        });
        showMessage(`Deleted ${data.deleted_count} note(s)`, "success");
      } else {
        const data = await response.json();
        showMessage(data.error || "Failed to delete notes");
      }
    } catch (error) {
      showMessage("Network error, please try again");
    } finally {
      clearAllNotesBtn.disabled = false;
      clearAllNotesBtn.textContent = "Delete all notes";
    }
  });
}
