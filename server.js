const express = require("express");
const path = require("path");
const Datastore = require("nedb");

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize NeDB database
const flashcardsDB = new Datastore({
  filename: "flashcards.db",
  autoload: true,
});

// Middleware to parse JSON bodies
app.use(express.json());

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, "public")));

app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

// API endpoint to add flashcards
app.post("/api/flashcards", (req, res) => {
  const flashcards = req.body;
  if (!Array.isArray(flashcards)) {
    return res
      .status(400)
      .json({ message: "Request body must be an array of flashcards." });
  }

  const flashcardsToInsert = flashcards
    .map((card) => {
      let word,
        meaning,
        imageUrl = null;
      if (Array.isArray(card)) {
        // Old format: ["word", "meaning"]
        word = card[0];
        meaning = card[1];
      } else if (typeof card === "object" && card !== null) {
        // New format: {word: "...", meaning: "...", imageUrl: "..."}
        word = card.word;
        meaning = card.meaning;
        imageUrl = card.imageUrl || null;
      } else {
        console.warn("Invalid flashcard format found in array:", card);
        return null;
      }

      if (!word || !meaning) {
        console.warn("Flashcard missing word or meaning:", card);
        return null;
      }

      return {
        word: word,
        meaning: meaning,
        imageUrl: imageUrl,
        easeFactor: 2.5,
        interval: 0,
        repetitions: 0,
        nextReviewDate: new Date(),
      };
    })
    .filter((card) => card !== null);

  if (flashcardsToInsert.length === 0) {
    return res
      .status(400)
      .json({ message: "No valid flashcards provided to insert." });
  }

  flashcardsDB.insert(flashcardsToInsert, (err, newDocs) => {
    if (err) {
      console.error("Error inserting flashcards:", err);
      return res
        .status(500)
        .json({ message: "Failed to add flashcards.", error: err.message });
    }
    res.status(201).json({
      message: `Successfully added ${newDocs.length} flashcards.`,
      count: newDocs.length,
    });
  });
});

// API endpoint to lookup definition from Oxford Dictionary (proxy)
app.get("/api/lookup-definition", async (req, res) => {
  const word_id = req.query.word; // The word to lookup

  // IMPORTANT: Replace with your actual Oxford Dictionary API App ID and App Key
  // These should ideally be stored in environment variables (e.g., process.env.OXFORD_APP_ID)
  const app_id = "YOUR_OXFORD_APP_ID";
  const app_key = "YOUR_OXFORD_APP_KEY";

  if (
    !app_id ||
    !app_key ||
    app_id === "YOUR_OXFORD_APP_ID" ||
    app_key === "YOUR_OXFORD_APP_KEY"
  ) {
    return res.status(400).json({
      message:
        "Oxford API App ID or App Key not configured. Please get them from developer.oxforddictionaries.com.",
    });
  }

  if (!word_id) {
    return res
      .status(400)
      .json({ message: "Missing word parameter for definition lookup." });
  }

  const options = {
    hostname: "od-api.oxforddictionaries.com",
    port: 443,
    path: `/api/v2/entries/en-us/${word_id.toLowerCase()}`, // Using en-us for English-US
    method: "GET",
    headers: {
      app_id: app_id,
      app_key: app_key,
    },
  };

  const https = require("https");
  https
    .get(options, (apiRes) => {
      let data = "";
      apiRes.on("data", (chunk) => {
        data += chunk;
      });
      apiRes.on("end", () => {
        try {
          const parsedData = JSON.parse(data);
          res.status(apiRes.statusCode).json(parsedData);
        } catch (parseError) {
          console.error("Error parsing Oxford API response:", parseError);
          res
            .status(500)
            .json({ message: "Error processing dictionary response." });
        }
      });
    })
    .on("error", (apiError) => {
      console.error("Error calling Oxford API:", apiError);
      res.status(500).json({
        message: "Failed to connect to dictionary service.",
        error: apiError.message,
      });
    });
});

// API endpoint to get all flashcards (with optional limit and review date filtering)
app.get("/api/flashcards", (req, res) => {
  const limit = parseInt(req.query.limit) || 0;
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  let query = { nextReviewDate: { $lte: today } }; // Only fetch cards due for review today or earlier

  let cursor = flashcardsDB.find(query).sort({ nextReviewDate: 1 }); // Sort by next review date

  if (limit > 0) {
    cursor = cursor.limit(limit);
  }

  cursor.exec((err, docs) => {
    if (err) {
      console.error("Error fetching flashcards:", err);
      return res.status(500).json({
        message: "Failed to retrieve flashcards.",
        error: err.message,
      });
    }
    res.status(200).json(docs);
  });
});

// API endpoint to update flashcard progress
app.put("/api/flashcards/:id", (req, res) => {
  const cardId = req.params.id;
  const { easeFactor, interval, repetitions, nextReviewDate } = req.body;

  // Basic validation
  if (
    typeof easeFactor === "undefined" ||
    typeof interval === "undefined" ||
    typeof repetitions === "undefined" ||
    typeof nextReviewDate === "undefined"
  ) {
    return res.status(400).json({ message: "Missing progress fields." });
  }

  flashcardsDB.update(
    { _id: cardId },
    {
      $set: {
        easeFactor,
        interval,
        repetitions,
        nextReviewDate: new Date(nextReviewDate),
      },
    },
    {},
    (err, numReplaced) => {
      if (err) {
        console.error("Error updating flashcard progress:", err);
        return res.status(500).json({
          message: "Failed to update flashcard progress.",
          error: err.message,
        });
      }
      if (numReplaced === 0) {
        return res.status(404).json({ message: "Flashcard not found." });
      }
      res
        .status(200)
        .json({ message: "Flashcard progress updated successfully." });
    }
  );
});

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
