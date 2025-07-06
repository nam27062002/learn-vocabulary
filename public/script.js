// Bỏ trống để bắt đầu, sau này sẽ thêm logic JavaScript

document.addEventListener("DOMContentLoaded", () => {
  const flashcardInput = document.getElementById("flashcard-input");
  const importButton = document.getElementById("import-button");
  const importMessage = document.getElementById("import-message");

  importButton.addEventListener("click", async () => {
    const inputText = flashcardInput.value.trim();
    if (!inputText) {
      importMessage.textContent = "Please enter flashcard data.";
      importMessage.style.color = "red";
      return;
    }

    try {
      // Assuming the input is a JSON array of ["word", "meaning"]
      const flashcards = JSON.parse(inputText);

      if (
        !Array.isArray(flashcards) ||
        flashcards.some((card) => !Array.isArray(card) || card.length !== 2)
      ) {
        importMessage.textContent =
          'Invalid flashcard format. Please use JSON array of ["word", "meaning"].';
        importMessage.style.color = "red";
        return;
      }

      const response = await fetch("/api/flashcards", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(flashcards),
      });

      const data = await response.json();

      if (response.ok) {
        importMessage.textContent = data.message;
        importMessage.style.color = "green";
        flashcardInput.value = ""; // Clear input after successful import
      } else {
        importMessage.textContent = `Error: ${
          data.message || response.statusText
        }`;
        importMessage.style.color = "red";
      }
    } catch (error) {
      importMessage.textContent = `Error parsing input or sending data: ${error.message}`;
      importMessage.style.color = "red";
      console.error("Import error:", error);
    }
  });
});

// Learning Section Logic
const flashcardDisplay = document.getElementById("flashcard-display");
const vietnameseMeaning = document.getElementById("vietnamese-meaning");
const englishInput = document.getElementById("english-input");
const hintButton = document.getElementById("hint-button");
const hintDisplay = document.getElementById("hint-display");
const checkButton = document.getElementById("check-button");
const feedbackMessage = document.getElementById("feedback-message");
const nextButton = document.getElementById("next-button");
const learningMessage = document.getElementById("learning-message");

const dailyLimitInput = document.getElementById("daily-limit");
const startLearningButton = document.getElementById("start-learning-button");

const vietToEngMode = document.getElementById("viet-to-eng");
const engToVietMode = document.getElementById("eng-to-viet");

// New Flashcard Section Elements for dynamic addition
const newFlashcardsContainer = document.getElementById(
  "new-flashcards-container"
);
const addNewCardButton = document.getElementById("add-new-card-button");
const saveAllCardsButton = document.getElementById("save-all-cards-button");
const addCardMessage = document.getElementById("add-card-message"); // Re-using this for overall add message

let flashcards = [];
let currentFlashcardIndex = 0;
let currentLearningMode = "vietToEng"; // Default mode
let newCardCounter = 0; // To keep track of unique IDs for new cards

async function loadFlashcards(limit = 0) {
  try {
    const url =
      limit > 0 ? `/api/flashcards?limit=${limit}` : "/api/flashcards";
    const response = await fetch(url);
    const data = await response.json();
    flashcards = data;

    if (flashcards.length > 0) {
      currentFlashcardIndex = 0; // Reset index for new session
      flashcardDisplay.style.display = "block"; // Show learning section
      displayFlashcard();
      learningMessage.textContent = "";
    } else {
      learningMessage.textContent =
        "No flashcards available. Please import some first or adjust the limit!";
      flashcardDisplay.style.display = "none";
    }
  } catch (error) {
    learningMessage.textContent = `Error loading flashcards: ${error.message}`;
    learningMessage.style.color = "red";
    console.error("Load flashcards error:", error);
  }
}

function displayFlashcard() {
  if (currentFlashcardIndex < flashcards.length) {
    const card = flashcards[currentFlashcardIndex];

    if (currentLearningMode === "vietToEng") {
      vietnameseMeaning.textContent = card.meaning;
      englishInput.placeholder = "Type English word";
    } else {
      // engToViet
      vietnameseMeaning.textContent = card.word;
      englishInput.placeholder = "Type Vietnamese meaning";
    }

    // Display image if available
    const imageElement = document.getElementById("flashcard-image");
    if (card.imageUrl && imageElement) {
      imageElement.src = card.imageUrl;
      imageElement.style.display = "block";
    } else if (imageElement) {
      imageElement.style.display = "none"; // Hide if no image
      imageElement.src = "";
    }

    englishInput.value = "";
    feedbackMessage.textContent = "";
    hintDisplay.textContent = "";
    nextButton.style.display = "none";
    checkButton.style.display = "inline-block";
    englishInput.disabled = false;
    englishInput.focus();
  } else {
    learningMessage.textContent =
      "You have completed all flashcards for today!";
    flashcardDisplay.style.display = "none";
  }
}

// Function to create a new flashcard entry HTML
function createNewCardEntry() {
  newCardCounter++;
  const cardId = `new-card-${newCardCounter}`;

  const cardHtml = `
    <div class="new-card-entry" id="${cardId}">
      <div class="card-header">
        <span class="card-number">${newCardCounter}</span>
        <button class="delete-card-button" data-card-id="${cardId}">&times;</button>
      </div>
      <div class="card-inputs">
        <div class="card-input-group">
          <label for="word-${cardId}">THUẬT NGỮ</label>
          <input type="text" id="word-${cardId}" placeholder="English Word">
          <button class="lookup-definition-button" data-card-id="${cardId}">Lookup Definition</button>
        </div>
        <div class="card-input-group">
          <label for="meaning-${cardId}">ĐỊNH NGHĨA</label>
          <textarea id="meaning-${cardId}" placeholder="Vietnamese Meaning" rows="2"></textarea>
          <div class="definition-suggestions" id="suggestions-${cardId}"></div>
        </div>
        <div class="card-input-group">
          <label>HÌNH ẢNH</label>
          <div class="image-placeholder" data-card-id="${cardId}">
            <img id="image-${cardId}" src="" alt="Flashcard Image">
            <span>Hình ảnh</span>
          </div>
        </div>
      </div>
    </div>
  `;
  newFlashcardsContainer.insertAdjacentHTML("beforeend", cardHtml);

  // Attach delete event listener
  const deleteButton = document.querySelector(`#${cardId} .delete-card-button`);
  deleteButton.addEventListener("click", (event) => {
    const cardToRemove = document.getElementById(event.target.dataset.cardId);
    cardToRemove.remove();
    updateCardNumbers();
    toggleSaveButtonVisibility();
  });

  // For now, image placeholder does nothing. Later, this will trigger image search.
  const imagePlaceholder = document.querySelector(
    `#${cardId} .image-placeholder`
  );
  imagePlaceholder.addEventListener("click", () => {
    alert("Chức năng tìm kiếm hình ảnh sẽ được thêm sau!");
  });

  // Attach lookup definition event listener
  const lookupButton = document.querySelector(
    `#${cardId} .lookup-definition-button`
  );
  lookupButton.addEventListener("click", async () => {
    const wordInput = document.getElementById(`word-${cardId}`);
    const meaningTextarea = document.getElementById(`meaning-${cardId}`);
    const suggestionsDiv = document.getElementById(`suggestions-${cardId}`);
    const wordToLookup = wordInput.value.trim();

    if (!wordToLookup) {
      suggestionsDiv.innerHTML =
        '<span style="color: red;">Please enter a word to lookup.</span>';
      return;
    }

    suggestionsDiv.innerHTML =
      '<span style="color: gray;">Searching for definitions...</span>';

    try {
      const response = await fetch(
        `/api/lookup-definition?word=${encodeURIComponent(wordToLookup)}`
      );
      const data = await response.json();

      if (response.ok) {
        if (data.results && data.results.length > 0) {
          suggestionsDiv.innerHTML = "";
          const definitions = parseOxfordDefinition(data);
          if (definitions.length > 0) {
            definitions.forEach((def, index) => {
              const defItem = document.createElement("div");
              defItem.classList.add("definition-item");
              defItem.innerHTML = `<strong>${index + 1}.</strong> ${def}`; // Using innerHTML for basic formatting like bold
              defItem.style.cursor = "pointer";
              defItem.style.padding = "5px 0";
              defItem.style.borderBottom = "1px solid #4a505b";
              defItem.style.marginBottom = "5px";
              defItem.addEventListener("click", () => {
                meaningTextarea.value = def.trim();
                suggestionsDiv.innerHTML = ""; // Clear suggestions after selection
              });
              suggestionsDiv.appendChild(defItem);
            });
            suggestionsDiv.insertAdjacentHTML(
              "beforeend",
              '<p style="font-size: 0.8em; color: #a0a8b4;">Click on a definition to use it.</p>'
            );
          } else {
            suggestionsDiv.innerHTML =
              '<span style="color: orange;">No definitions found for this word.</span>';
          }
        } else {
          suggestionsDiv.innerHTML =
            '<span style="color: orange;">No definitions found for this word.</span>';
        }
      } else {
        suggestionsDiv.innerHTML = `<span style="color: red;">Error: ${
          data.message || response.statusText
        }</span>`;
      }
    } catch (error) {
      suggestionsDiv.innerHTML =
        '<span style="color: red;">An error occurred while looking up definition.</span>';
      console.error("Definition lookup error:", error);
    }
  });

  toggleSaveButtonVisibility();
}

// Update card numbers after deletion
function updateCardNumbers() {
  const cardEntries =
    newFlashcardsContainer.querySelectorAll(".new-card-entry");
  cardEntries.forEach((entry, index) => {
    entry.querySelector(".card-number").textContent = index + 1;
    entry.id = `new-card-${index + 1}`;
    entry
      .querySelector('label[for^="word-"]')
      .setAttribute("for", `word-new-card-${index + 1}`);
    entry.querySelector('input[id^="word-"]').id = `word-new-card-${index + 1}`;
    entry
      .querySelector('label[for^="meaning-"]')
      .setAttribute("for", `meaning-new-card-${index + 1}`);
    entry.querySelector('textarea[id^="meaning-"]').id = `meaning-new-card-${
      index + 1
    }`;
    entry.querySelector(".image-placeholder").dataset.cardId = `new-card-${
      index + 1
    }`;
    entry.querySelector('img[id^="image-"]').id = `image-new-card-${index + 1}`;
    entry.querySelector(".delete-card-button").dataset.cardId = `new-card-${
      index + 1
    }`;
  });
  newCardCounter = cardEntries.length;
}

// Show/hide Save All Cards button
function toggleSaveButtonVisibility() {
  if (newFlashcardsContainer.children.length > 0) {
    saveAllCardsButton.style.display = "inline-block";
  } else {
    saveAllCardsButton.style.display = "none";
  }
}

// Event Listeners for new card section
addNewCardButton.addEventListener("click", createNewCardEntry);

saveAllCardsButton.addEventListener("click", async () => {
  const cardsToSave = [];
  const cardEntries =
    newFlashcardsContainer.querySelectorAll(".new-card-entry");

  let hasError = false;
  cardEntries.forEach((entry) => {
    const wordInput = entry.querySelector('input[id^="word-"]');
    const meaningTextarea = entry.querySelector('textarea[id^="meaning-"]');
    const imageElement = entry.querySelector('img[id^="image-"]');

    const word = wordInput.value.trim();
    const meaning = meaningTextarea.value.trim();
    const imageUrl = imageElement.src ? imageElement.src.trim() : "";

    if (!word || !meaning) {
      addCardMessage.textContent =
        "Error: Please fill in both Term and Definition for all cards.";
      addCardMessage.style.color = "red";
      hasError = true;
      return;
    }

    const newCard = { word, meaning };
    if (imageUrl) {
      newCard.imageUrl = imageUrl;
    }
    cardsToSave.push(newCard);
  });

  if (hasError) {
    return;
  }

  if (cardsToSave.length === 0) {
    addCardMessage.textContent = "No new flashcards to save.";
    addCardMessage.style.color = "orange";
    return;
  }

  try {
    const response = await fetch("/api/flashcards", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(cardsToSave),
    });

    const data = await response.json();

    if (response.ok) {
      addCardMessage.textContent = data.message;
      addCardMessage.style.color = "green";
      newFlashcardsContainer.innerHTML = ""; // Clear all entries
      toggleSaveButtonVisibility();
      newCardCounter = 0; // Reset counter
      // Optionally, reload flashcards to include the new ones in learning session if needed
      // await loadFlashcards(parseInt(dailyLimitInput.value));
    } else {
      addCardMessage.textContent = `Error: ${
        data.message || response.statusText
      }`;
      addCardMessage.style.color = "red";
    }
  } catch (error) {
    addCardMessage.textContent = `Error saving flashcards: ${error.message}`;
    addCardMessage.style.color = "red";
    console.error("Save flashcards error:", error);
  }
});

hintButton.addEventListener("click", () => {
  if (currentFlashcardIndex < flashcards.length) {
    const currentCard = flashcards[currentFlashcardIndex];
    let hintText = "";
    if (currentLearningMode === "vietToEng") {
      hintText = currentCard.word;
    } else {
      hintText = currentCard.meaning;
    }

    if (hintText.length > 0) {
      hintDisplay.textContent = `Hint: ${hintText[0].toUpperCase()}`;
    }
  }
});

checkButton.addEventListener("click", async () => {
  if (currentFlashcardIndex < flashcards.length) {
    const currentCard = flashcards[currentFlashcardIndex];
    let correctAnswer = "";
    if (currentLearningMode === "vietToEng") {
      correctAnswer = currentCard.word.toLowerCase();
    } else {
      correctAnswer = currentCard.meaning.toLowerCase();
    }
    const userAnswer = englishInput.value.trim().toLowerCase();

    let isCorrect = userAnswer === correctAnswer;

    // SM-2 algorithm variables
    let newEaseFactor = currentCard.easeFactor;
    let newInterval = currentCard.interval;
    let newRepetitions = currentCard.repetitions;
    let newNextReviewDate = new Date();

    if (isCorrect) {
      feedbackMessage.textContent = "Correct!";
      feedbackMessage.style.color = "green";

      newRepetitions++;
      if (newRepetitions === 1) {
        newInterval = 1;
      } else if (newRepetitions === 2) {
        newInterval = 6;
      } else {
        newInterval = Math.round(newInterval * newEaseFactor);
      }
      newEaseFactor = Math.min(3.0, newEaseFactor + 0.1);
    } else {
      feedbackMessage.textContent = `Incorrect. The correct answer was: ${correctAnswer}`;
      feedbackMessage.style.color = "red";

      newRepetitions = 0;
      newInterval = 1; // Reset interval to 1 day on incorrect answer
      newEaseFactor = Math.max(1.3, newEaseFactor - 0.2);
    }

    // Calculate next review date
    newNextReviewDate.setDate(newNextReviewDate.getDate() + newInterval);

    // Update UI state
    englishInput.disabled = true;
    checkButton.style.display = "none";
    nextButton.style.display = "inline-block";

    // Send update to backend
    try {
      const response = await fetch(`/api/flashcards/${currentCard._id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          easeFactor: newEaseFactor,
          interval: newInterval,
          repetitions: newRepetitions,
          nextReviewDate: newNextReviewDate.toISOString(),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error(
          "Failed to update flashcard progress:",
          errorData.message
        );
        // Optionally, show a user-friendly error message
      }
    } catch (error) {
      console.error("Error sending progress update:", error);
      // Optionally, show a user-friendly error message
    }
  }
});

nextButton.addEventListener("click", () => {
  currentFlashcardIndex++;
  displayFlashcard();
});

startLearningButton.addEventListener("click", () => {
  const limit = parseInt(dailyLimitInput.value);
  if (isNaN(limit) || limit <= 0) {
    learningMessage.textContent =
      "Please enter a valid number for daily limit.";
    learningMessage.style.color = "red";
    return;
  }
  currentLearningMode = document.querySelector(
    'input[name="learningMode"]:checked'
  ).value;
  loadFlashcards(limit);
});

// Initially hide the flashcard display until a session starts
flashcardDisplay.style.display = "none";

// Helper function to parse Oxford Dictionary API response for definitions
function parseOxfordDefinition(data) {
  const definitions = [];
  if (data && data.results) {
    data.results.forEach((result) => {
      if (result.lexicalEntries) {
        result.lexicalEntries.forEach((lexicalEntry) => {
          if (lexicalEntry.entries) {
            lexicalEntry.entries.forEach((entry) => {
              if (entry.senses) {
                entry.senses.forEach((sense) => {
                  if (sense.definitions) {
                    definitions.push(...sense.definitions);
                  } else if (sense.short_definitions) {
                    // Fallback to short definitions
                    definitions.push(...sense.short_definitions);
                  }
                });
              }
            });
          }
        });
      }
    });
  }
  return definitions;
}
