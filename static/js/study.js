// study.js - handles study session with multiple modes

(function () {
  // Existing elements
  const deckStudyOptions = document.getElementById("deckStudyOptions");
  const studyArea = document.getElementById("studyArea");
  const cardWordEl = document.getElementById("cardWord");
  const cardPhoneticEl = document.getElementById("cardPhonetic");
  const cardImageEl = document.getElementById("cardImage");
  const cardDefsEl = document.getElementById("cardDefs");
  const favoriteButton = document.getElementById("favoriteButton");
  const answerArea = document.getElementById("answerSection") || {
    innerHTML: "",
    appendChild: () => {},
    style: {},
  };
  const feedbackMsg = document.getElementById("feedbackMsg") || {
    style: {},
    textContent: "",
  };
  const noCardMsg = document.getElementById("noCardMsg") || { style: {} };
  const optionsArea = document.getElementById("optionsArea") || answerArea;
  const backBtn = document.getElementById("backBtn");
  const statsInfo = document.getElementById("statsInfo");
  const studyHeader = document.querySelector(".study-header");

  const audioButton = document.getElementById("audioButton");
  const audioToggle = document.getElementById("audioToggle");

  // Timer elements
  const timerDisplay = document.getElementById("timerDisplay");
  const timerText = document.getElementById("timerText");

  // Function to abbreviate part of speech
  function abbreviatePartOfSpeech(partOfSpeech) {
    if (!partOfSpeech) return '';
    
    const abbreviations = {
      'noun': 'n',
      'verb': 'v',
      'adjective': 'adj',
      'adverb': 'adv',
      'pronoun': 'pron',
      'preposition': 'prep',
      'conjunction': 'conj',
      'interjection': 'interj',
      'determiner': 'det',
      'auxiliary': 'aux',
      'modal': 'modal',
      'article': 'art',
      'numeral': 'num',
      'participle': 'part',
      'gerund': 'ger',
      'infinitive': 'inf'
    };
    
    const lower = partOfSpeech.toLowerCase();
    return abbreviations[lower] || partOfSpeech;
  }

  // Audio feedback system
  const AudioFeedback = {
    correctSound: null,
    incorrectSound: null,
    enabled: true,
    audioContext: null,
    userInteracted: false,

    init() {
      try {
        console.log("🎵 Initializing audio feedback system...");

        // Try to load audio files - fallback to WAV if MP3 fails
        this.correctSound = new Audio();
        this.incorrectSound = new Audio();

        // Set up sources with fallbacks
        this.setupAudioSources();

        console.log("🎵 Audio objects created, setting up event listeners...");

        // Set volume levels
        this.correctSound.volume = 0.6;
        this.incorrectSound.volume = 0.6;

        // Add error event listeners
        this.correctSound.addEventListener("error", (e) => {
          console.error("❌ Failed to load correct sound:", e);
          console.error("❌ Error details:", {
            error: e.error,
            message: e.message,
            type: e.type,
            target: e.target,
          });
          this.correctSound = null;
        });

        this.incorrectSound.addEventListener("error", (e) => {
          console.error("❌ Failed to load incorrect sound:", e);
          console.error("❌ Error details:", {
            error: e.error,
            message: e.message,
            type: e.type,
            target: e.target,
          });
          this.incorrectSound = null;
        });

        // Add load event listeners for debugging
        this.correctSound.addEventListener("loadeddata", () => {
          console.log("✅ Correct sound loaded successfully");
        });

        this.incorrectSound.addEventListener("loadeddata", () => {
          console.log("✅ Incorrect sound loaded successfully");
        });

        // Add additional debugging events
        this.correctSound.addEventListener("loadstart", () => {
          console.log("🔄 Started loading correct sound...");
        });

        this.incorrectSound.addEventListener("loadstart", () => {
          console.log("🔄 Started loading incorrect sound...");
        });

        this.correctSound.addEventListener("canplay", () => {
          console.log("🎵 Correct sound can start playing");
        });

        this.incorrectSound.addEventListener("canplay", () => {
          console.log("🎵 Incorrect sound can start playing");
        });

        // Load saved preference from localStorage
        const savedPreference = localStorage.getItem("audioFeedbackEnabled");
        if (savedPreference !== null) {
          this.enabled = savedPreference === "true";
        }

        // Update toggle state
        if (audioToggle) {
          audioToggle.checked = this.enabled;
          audioToggle.addEventListener("change", (e) => {
            this.enabled = e.target.checked;
            localStorage.setItem(
              "audioFeedbackEnabled",
              this.enabled.toString()
            );
            console.log(
              "Audio feedback",
              this.enabled ? "enabled" : "disabled"
            );
          });
        }

        // Set up user interaction detection for autoplay policy
        this.setupUserInteractionDetection();

        // Check if audio files exist before preloading
        this.checkAudioFiles().then(() => {
          // Preload audio files
          this.preloadAudio();
        });

        console.log(
          "Audio feedback system initialized. Enabled:",
          this.enabled
        );
      } catch (error) {
        console.error("Failed to initialize audio feedback system:", error);
        this.enabled = false;
      }
    },

    setupAudioSources() {
      console.log("🔧 Setting up audio sources...");

      // Try MP3 first, then fallback to creating simple audio tones
      this.correctSound.addEventListener("error", () => {
        console.warn(
          "🔄 MP3 failed, creating fallback audio for correct sound"
        );
        this.createFallbackAudio("correct");
      });

      this.incorrectSound.addEventListener("error", () => {
        console.warn(
          "🔄 MP3 failed, creating fallback audio for incorrect sound"
        );
        this.createFallbackAudio("incorrect");
      });

      // Set the source
      this.correctSound.src = "/static/audio/correct.wav";
      this.incorrectSound.src = "/static/audio/incorrect.wav";
    },

    createFallbackAudio(type) {
      console.log(`🎵 Creating fallback ${type} audio using Web Audio API...`);

      try {
        if (!this.audioContext) {
          this.audioContext = new (window.AudioContext ||
            window.webkitAudioContext)();
        }

        const duration = type === "correct" ? 0.6 : 0.4;
        const frequencies =
          type === "correct" ? [523.25, 659.25, 783.99] : [220.0, 246.94];

        // Create audio buffer
        const sampleRate = this.audioContext.sampleRate;
        const buffer = this.audioContext.createBuffer(
          1,
          duration * sampleRate,
          sampleRate
        );
        const data = buffer.getChannelData(0);

        // Generate tone
        for (let i = 0; i < buffer.length; i++) {
          let sample = 0;
          for (const freq of frequencies) {
            sample += Math.sin((2 * Math.PI * freq * i) / sampleRate);
          }
          data[i] = (sample / frequencies.length) * 0.3; // Volume control

          // Apply fade in/out
          const fadeFrames = sampleRate * 0.01; // 10ms fade
          if (i < fadeFrames) {
            data[i] *= i / fadeFrames;
          } else if (i > buffer.length - fadeFrames) {
            data[i] *= (buffer.length - i) / fadeFrames;
          }
        }

        // Store the buffer for playback
        if (type === "correct") {
          this.correctSoundBuffer = buffer;
          this.correctSound = null; // Use buffer instead
        } else {
          this.incorrectSoundBuffer = buffer;
          this.incorrectSound = null; // Use buffer instead
        }

        console.log(`✅ Fallback ${type} audio created successfully`);
      } catch (error) {
        console.error(`❌ Failed to create fallback ${type} audio:`, error);
      }
    },

    async checkAudioFiles() {
      console.log("🔍 Checking audio file accessibility...");

      try {
        // Check correct sound file
        const correctResponse = await fetch("/static/audio/correct.wav", {
          method: "HEAD",
        });
        if (correctResponse.ok) {
          console.log("✅ correct.mp3 is accessible");
          console.log(
            "📋 Content-Type:",
            correctResponse.headers.get("content-type")
          );
          console.log(
            "📏 Content-Length:",
            correctResponse.headers.get("content-length")
          );
        } else {
          console.error(
            "❌ correct.mp3 not accessible:",
            correctResponse.status,
            correctResponse.statusText
          );
        }

        // Check incorrect sound file
        const incorrectResponse = await fetch("/static/audio/incorrect.wav", {
          method: "HEAD",
        });
        if (incorrectResponse.ok) {
          console.log("✅ incorrect.mp3 is accessible");
          console.log(
            "📋 Content-Type:",
            incorrectResponse.headers.get("content-type")
          );
          console.log(
            "📏 Content-Length:",
            incorrectResponse.headers.get("content-length")
          );
        } else {
          console.error(
            "❌ incorrect.mp3 not accessible:",
            incorrectResponse.status,
            incorrectResponse.statusText
          );
        }

        // Test if we can actually load the audio data
        await this.testAudioLoad();
      } catch (error) {
        console.error("❌ Error checking audio files:", error);
      }
    },

    async testAudioLoad() {
      console.log("🧪 Testing actual audio loading...");

      return new Promise((resolve) => {
        const testAudio = new Audio("/static/audio/correct.mp3");

        testAudio.addEventListener("loadeddata", () => {
          console.log("✅ Test audio loaded successfully");
          console.log("⏱️ Duration:", testAudio.duration);
          console.log("🔊 Ready state:", testAudio.readyState);
          resolve();
        });

        testAudio.addEventListener("error", (e) => {
          console.error("❌ Test audio failed to load:", e);
          console.error("🔍 Audio error code:", testAudio.error?.code);
          console.error("🔍 Audio error message:", testAudio.error?.message);
          resolve();
        });

        testAudio.load();
      });
    },

    setupUserInteractionDetection() {
      // Listen for first user interaction to enable audio
      const enableAudio = () => {
        this.userInteracted = true;
        console.log("🎵 User interaction detected - audio enabled");

        // Try to create audio context if needed
        if (!this.audioContext && window.AudioContext) {
          try {
            this.audioContext = new (window.AudioContext ||
              window.webkitAudioContext)();
            console.log("🎵 Audio context created");
          } catch (e) {
            console.warn("Could not create audio context:", e);
          }
        }

        // Remove listeners after first interaction
        document.removeEventListener("click", enableAudio);
        document.removeEventListener("keydown", enableAudio);
        document.removeEventListener("touchstart", enableAudio);
      };

      // Add listeners for user interaction
      document.addEventListener("click", enableAudio, { once: true });
      document.addEventListener("keydown", enableAudio, { once: true });
      document.addEventListener("touchstart", enableAudio, { once: true });
    },

    preloadAudio() {
      // Preload audio files to avoid delays
      if (this.correctSound) {
        this.correctSound.load();
      }
      if (this.incorrectSound) {
        this.incorrectSound.load();
      }
    },

    playCorrect() {
      if (!this.enabled) {
        console.log("🔇 Audio feedback disabled");
        return;
      }

      try {
        if (this.correctSound && this.correctSound.src) {
          // Use MP3 file
          this.correctSound.currentTime = 0;
          const playPromise = this.correctSound.play();

          if (playPromise !== undefined) {
            playPromise
              .then(() => {
                console.log("🎵 ✅ Playing correct answer sound (MP3)");
              })
              .catch((err) => {
                console.warn(
                  "🔇 MP3 play failed, trying fallback:",
                  err.message
                );
                this.playFallbackAudio("correct");
              });
          }
        } else if (this.correctSoundBuffer) {
          // Use fallback audio buffer
          this.playFallbackAudio("correct");
        } else {
          console.warn("❌ No correct sound available");
          this.showAudioFeedbackMessage("✅ Correct!", "success");
        }
      } catch (error) {
        console.error("❌ Error playing correct sound:", error);
        this.showAudioFeedbackMessage("✅ Correct!", "success");
      }
    },

    playIncorrect() {
      if (!this.enabled) {
        console.log("🔇 Audio feedback disabled");
        return;
      }

      try {
        if (this.incorrectSound && this.incorrectSound.src) {
          // Use MP3 file
          this.incorrectSound.currentTime = 0;
          const playPromise = this.incorrectSound.play();

          if (playPromise !== undefined) {
            playPromise
              .then(() => {
                console.log("🎵 ❌ Playing incorrect answer sound (MP3)");
              })
              .catch((err) => {
                console.warn(
                  "🔇 MP3 play failed, trying fallback:",
                  err.message
                );
                this.playFallbackAudio("incorrect");
              });
          }
        } else if (this.incorrectSoundBuffer) {
          // Use fallback audio buffer
          this.playFallbackAudio("incorrect");
        } else {
          console.warn("❌ No incorrect sound available");
          this.showAudioFeedbackMessage("❌ Try again!", "error");
        }
      } catch (error) {
        console.error("❌ Error playing incorrect sound:", error);
        this.showAudioFeedbackMessage("❌ Try again!", "error");
      }
    },

    playFallbackAudio(type) {
      try {
        if (!this.audioContext) {
          console.warn("❌ No audio context available for fallback");
          this.showAudioFeedbackMessage(
            type === "correct" ? "✅ Correct!" : "❌ Try again!",
            type === "correct" ? "success" : "error"
          );
          return;
        }

        const buffer =
          type === "correct"
            ? this.correctSoundBuffer
            : this.incorrectSoundBuffer;

        if (!buffer) {
          console.warn(`❌ No ${type} buffer available`);
          this.showAudioFeedbackMessage(
            type === "correct" ? "✅ Correct!" : "❌ Try again!",
            type === "correct" ? "success" : "error"
          );
          return;
        }

        // Create buffer source
        const source = this.audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(this.audioContext.destination);

        // Play the sound
        source.start(0);
        console.log(
          `🎵 ${
            type === "correct" ? "✅" : "❌"
          } Playing ${type} answer sound (fallback)`
        );
      } catch (error) {
        console.error(`❌ Error playing fallback ${type} sound:`, error);
        this.showAudioFeedbackMessage(
          type === "correct" ? "✅ Correct!" : "❌ Try again!",
          type === "correct" ? "success" : "error"
        );
      }
    },

    showAudioFeedbackMessage(message, type) {
      // Create a temporary visual feedback when audio fails
      const feedbackEl = document.createElement("div");
      feedbackEl.textContent = message;
      feedbackEl.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 10px 20px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
        z-index: 10000;
        transition: opacity 0.3s ease;
        ${
          type === "success"
            ? "background-color: #10b981;"
            : "background-color: #ef4444;"
        }
      `;

      document.body.appendChild(feedbackEl);

      // Remove after 2 seconds
      setTimeout(() => {
        feedbackEl.style.opacity = "0";
        setTimeout(() => {
          if (feedbackEl.parentNode) {
            feedbackEl.parentNode.removeChild(feedbackEl);
          }
        }, 300);
      }, 2000);
    },
  };

  // New elements for study mode selection
  const studyModeRadios = document.querySelectorAll('input[name="study_mode"]');
  const randomStudyOptions = document.getElementById("randomStudyOptions");
  const randomWordCountInput = document.getElementById("randomWordCount");
  const totalWordsAvailableSpan = document.getElementById(
    "totalWordsAvailable"
  );
  const startBtnDecks = document.getElementById("startBtn");
  const startBtnRandom = document.getElementById("startRandomBtn");
  const startBtnReview = document.getElementById("startReviewBtn");
  const reviewModeOption = document.getElementById("reviewModeOption");
  const reviewStudyOptions = document.getElementById("reviewStudyOptions");
  const reviewCount = document.getElementById("reviewCount");
  const reviewCountText = document.getElementById("reviewCountText");
  const reviewDetails = document.getElementById("reviewDetails");
  const mcCount = document.getElementById("mcCount");
  const typeCount = document.getElementById("typeCount");
  const dictationCount = document.getElementById("dictationCount");

  // Slider elements
  const modeSlider = document.getElementById("modeSlider");
  const sliderPrev = document.getElementById("sliderPrev");
  const sliderNext = document.getElementById("sliderNext");
  const indicators = document.querySelectorAll(".indicator");
  const modeSlides = document.querySelectorAll(".mode-slide");

  let correctCnt = 0,
    incorrectCnt = 0;
  let nextTimeout = null;
  let currentStudyMode = "decks"; // Default mode
  let seenCardIds = []; // To track cards seen in the current session for random mode
  let wordCount = 10; // Default word count for random mode

  // Hàm chuyển đổi từ loại sang viết tắt
  function getAbbreviatedPartOfSpeech(fullPartOfSpeech) {
    if (!fullPartOfSpeech) return "";
    const lowerCase = fullPartOfSpeech.toLowerCase();
    switch (lowerCase) {
      case "noun":
        return "n";
      case "verb":
        return "v";
      case "adjective":
        return "adj";
      case "adverb":
        return "adv";
      case "preposition":
        return "prep";
      case "conjunction":
        return "conj";
      case "pronoun":
        return "pron";
      case "interjection":
        return "interj";
      case "determiner":
        return "det";
      case "article":
        return "art";
      case "auxiliary verb":
        return "aux.v";
      default:
        return fullPartOfSpeech; // Trả về nguyên gốc nếu không tìm thấy viết tắt
    }
  }

  function updateStats() {
    if (statsInfo) {
      statsInfo.textContent = `${STUDY_CFG.labels.correct}: ${correctCnt} | ${STUDY_CFG.labels.incorrect}: ${incorrectCnt}`;
    }
  }

  let currentQuestion = null;
  let questionStartTime = null;

  // Study session timer variables
  let studyStartTime = null;
  let timerInterval = null;
  let timerPaused = false;
  let pausedTime = 0; // Total time spent paused
  let pauseStartTime = null; // When the current pause started

  // Study session timer functions
  function startStudyTimer() {
    console.log(`[DEBUG] Starting study session timer`);

    // Reset timer if already running
    if (timerInterval) {
      clearInterval(timerInterval);
    }

    // Set start time
    studyStartTime = Date.now();

    // Update timer display immediately
    updateTimerDisplay();

    // Start interval to update every second
    timerInterval = setInterval(updateTimerDisplay, 1000);

    // Show timer display
    if (timerDisplay) {
      timerDisplay.style.display = "flex";
    }
  }

  function stopStudyTimer() {
    console.log(`[DEBUG] Stopping study session timer`);

    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }

    // Hide timer display
    if (timerDisplay) {
      timerDisplay.style.display = "none";
    }
  }

  function resetStudyTimer() {
    console.log(`[DEBUG] Resetting study session timer`);

    stopStudyTimer();
    studyStartTime = null;

    // Reset pause-related variables
    timerPaused = false;
    pausedTime = 0;
    pauseStartTime = null;

    // Remove paused CSS class and reset styling
    if (timerDisplay) {
      timerDisplay.classList.remove('paused');
    }

    // Reset display to 00:00 and clear any paused styling
    if (timerText) {
      timerText.textContent = "00:00";
      timerText.style.color = '';
      timerText.style.opacity = '';
    }
  }

  function pauseStudyTimer() {
    if (!timerInterval || timerPaused) return;

    console.log(`[DEBUG] Pausing study session timer`);

    timerPaused = true;
    pauseStartTime = Date.now();

    // Clear the interval but keep studyStartTime
    clearInterval(timerInterval);
    timerInterval = null;

    // Add paused CSS class for visual indication
    if (timerDisplay) {
      timerDisplay.classList.add('paused');
    }

    // Update visual indication
    updateTimerDisplay();
  }

  function resumeStudyTimer() {
    if (!studyStartTime || !timerPaused) return;

    console.log(`[DEBUG] Resuming study session timer`);

    // Add the paused duration to total paused time
    if (pauseStartTime) {
      pausedTime += Date.now() - pauseStartTime;
      pauseStartTime = null;
    }

    timerPaused = false;

    // Remove paused CSS class
    if (timerDisplay) {
      timerDisplay.classList.remove('paused');
    }

    // Restart the interval
    timerInterval = setInterval(updateTimerDisplay, 1000);

    // Update display immediately
    updateTimerDisplay();
  }

  function updateTimerDisplay() {
    if (!studyStartTime || !timerText) return;

    let elapsed;
    if (timerPaused && pauseStartTime) {
      // If currently paused, don't include the current pause time
      elapsed = (pauseStartTime - studyStartTime) - pausedTime;
    } else {
      // Normal calculation, subtracting total paused time
      elapsed = (Date.now() - studyStartTime) - pausedTime;
    }

    // Ensure elapsed time is never negative
    elapsed = Math.max(0, elapsed);

    const totalSeconds = Math.floor(elapsed / 1000);

    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    let timeString;
    if (hours > 0) {
      // Format as HH:MM:SS for sessions longer than 1 hour
      timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    } else {
      // Format as MM:SS for sessions under 1 hour
      timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    // Add paused indicator if timer is paused
    if (timerPaused) {
      timeString += ' (Paused)';
      // Change timer color to indicate paused state
      if (timerText) {
        timerText.style.color = '#f59e0b'; // Orange color for paused state
        timerText.style.opacity = '0.8';
      }
    } else {
      // Reset timer color for active state
      if (timerText) {
        timerText.style.color = ''; // Reset to default
        timerText.style.opacity = '';
      }
    }

    timerText.textContent = timeString;
  }

  function getNextQuestion() {
    const params = new URLSearchParams();

    if (currentStudyMode === "random") {
      params.append("study_mode", "random");
      params.append("word_count", wordCount);
      seenCardIds.forEach((id) => params.append("seen_card_ids[]", id));
    } else if (currentStudyMode === "review") {
      params.append("study_mode", "review");
      seenCardIds.forEach((id) => params.append("seen_card_ids[]", id));
    } else if (currentStudyMode === "favorites") {
      params.append("study_mode", "favorites");
      seenCardIds.forEach((id) => params.append("seen_card_ids[]", id));
    } else {
      // Normal deck study mode
      const selectedDeckIds = Array.from(
        document.querySelectorAll('input[name="deck_ids"]:checked')
      ).map((cb) => cb.value);
      selectedDeckIds.forEach((id) => params.append("deck_ids[]", id));
      // Also send seen cards to prevent repetition in deck study mode
      seenCardIds.forEach((id) => params.append("seen_card_ids[]", id));
    }

    fetch(`${STUDY_CFG.nextUrl}?${params.toString()}`, {
      headers: {
        "X-CSRFToken": STUDY_CFG.csrfToken,
      },
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.done) {
          if (currentStudyMode === "review") {
            // Check if this is a session completion (all words resolved)
            if (data.session_completed) {
              console.log("Review session completed successfully!");
              showReviewCompletionModal();
              return;
            } else {
              // For review mode, loop back to the beginning instead of ending
              seenCardIds = []; // Reset seen cards to start over
              getNextQuestion(); // Restart the loop
              return;
            }
          } else if (currentStudyMode === "decks") {
            // For normal deck study, reset seen cards and continue infinitely
            console.log("All cards in selected decks have been studied. Restarting cycle...");
            seenCardIds = []; // Reset seen cards to start over
            getNextQuestion(); // Restart the cycle
            return;
          } else {
            noCardMsg.className = "no-cards-message show";
            studyArea.className = "study-area";
            return;
          }
        }

        // Add card ID to seen list for all study modes to prevent repetition
        if (data.question.id) {
          // Add card to seen list for all study modes to prevent repetition
          seenCardIds.push(data.question.id);
          console.log(`Added card ${data.question.id} to seen list. Total seen: ${seenCardIds.length}`);
        }

        renderQuestion(data.question);
      });
  }

  function renderQuestion(q) {
    // Auto-stop any active recording when switching to new card
    if (typeof VoiceRecording !== 'undefined' && VoiceRecording.isRecording) {
      console.log("🛑 Auto-stopping recording for new card");
      VoiceRecording.stopRecording();
    }
    
    // Reset border feedback NGAY LẬP TỨC
    const flashcardContainer = document.getElementById("cardBox");
    if (flashcardContainer) {
      flashcardContainer.classList.remove(
        "flashcard-correct",
        "flashcard-incorrect"
      );
      flashcardContainer.classList.remove("dictation-layout"); // giữ lại logic cũ
    }
    currentQuestion = q;
    questionStartTime = Date.now(); // Track when question was shown

    // Reset submission flag for new question
    window.submittingGrade = false;
    window.currentAnswerCorrectness = undefined;

    // Clear any existing timeout
    if (nextTimeout) {
      clearTimeout(nextTimeout);
      nextTimeout = null;
    }

    // Reset UI elements
    feedbackMsg.className = "feedback-message";

    if (cardWordEl) {
      cardWordEl.innerHTML = "";
    }
    if (cardPhoneticEl) {
      cardPhoneticEl.style.display = "none";
    }
    if (cardDefsEl) {
      cardDefsEl.className = "card-definitions";
    }

    // Hide grade buttons initially
    const gradeButtons = document.getElementById("gradeButtons");
    if (gradeButtons) {
      gradeButtons.className = "grade-buttons"; // Remove 'show' class to hide
      gradeButtons.classList.remove("show", "hidden"); // Clean up any extra classes
      gradeButtons.style.display = ""; // Clear inline styles to let CSS take over
      gradeButtons.style.visibility = ""; // Clear inline visibility
      console.log(`[DEBUG] Grade buttons hidden for new question`);
    }

    // Hide audio button during question phase - it will be shown after answer submission
    if (audioButton) {
      audioButton.style.display = "none";
    }
    
    // Hide recording controls during question phase
    const recordingControls = document.querySelector('.recording-controls');
    if (recordingControls) {
      recordingControls.style.display = 'none';
    }
    
    // Clear pronunciation feedback when moving to new card
    if (typeof VoiceRecording !== 'undefined') {
      VoiceRecording.clearRecording();
    }
    
    // Clear detailed input feedback from previous question
    const previousFeedback = document.querySelector('.detailed-input-feedback');
    if (previousFeedback) {
      previousFeedback.remove();
    }

    // Hide and reset favorite button during question phase - it will be shown after answer submission
    let currentFavoriteButton = favoriteButton;
    if (!currentFavoriteButton || !document.contains(currentFavoriteButton)) {
      console.log("[DEBUG] Favorite button reference is stale in renderQuestion, re-querying...");
      currentFavoriteButton = document.getElementById("favoriteButton");
    }

    if (currentFavoriteButton) {
      currentFavoriteButton.style.display = "none";

      // Reset favorite button to default state for new question
      const favoriteIcon = currentFavoriteButton.querySelector(".favorite-icon");
      if (favoriteIcon) {
        favoriteIcon.textContent = "🤍"; // Default unfavorited state
      }
      currentFavoriteButton.classList.remove("favorited");
      currentFavoriteButton.title = "Add to favorites";
      currentFavoriteButton.removeAttribute("data-card-id");

      console.log(`[DEBUG] Favorite button reset to default state for new question`);
    }

    // Remove any existing temporary audio containers
    const existingAudioContainer =
      document.getElementById("tempAudioContainer");
    if (existingAudioContainer) {
      existingAudioContainer.remove();
    }

    // Handle image display
    if (cardImageEl) {
      if (q.image_url) {
        cardImageEl.src = q.image_url;
        cardImageEl.style.display = "block";
      } else {
        cardImageEl.style.display = "none";
      }
    }

    // Clear previous options
    if (optionsArea) {
      optionsArea.innerHTML = "";
    }

    // Handle different question types
    if (q.type === "mc") {
      // Multiple choice mode - show definitions in the main word area
      if (cardWordEl && q.definitions && q.definitions.length > 0) {
        let defsText = "";
        
        q.definitions.forEach((def) => {
          if (def.english_definition) {
            defsText += `<div class="definition-item"><strong>${STUDY_CFG.labels.english_label}</strong> ${def.english_definition}</div>`;
          }
          if (def.vietnamese_definition) {
            defsText += `<div class="definition-item"><strong>${STUDY_CFG.labels.vietnamese_label}</strong> ${def.vietnamese_definition}</div>`;
          }
        });
        cardWordEl.innerHTML = defsText;
      }

      // Reset options area to grid mode for multiple choice
      if (optionsArea) {
        optionsArea.className = "options-area";
      }

      // Hide phonetic initially
      if (cardPhoneticEl) {
        cardPhoneticEl.style.display = "none";
      }

      // Hide definitions area for MC mode since we show them in word area
      if (cardDefsEl) {
        cardDefsEl.className = "card-definitions";
      }

      q.options.forEach((option) => {
        const btn = document.createElement("button");
        btn.textContent = option;
        btn.className = "option-btn";
        btn.addEventListener("click", () => {
          const correct = option === q.word;
          submitAnswer(correct);
        });
        optionsArea.appendChild(btn);
      });
    } else if (q.type === "dictation") {
      // Dictation mode - hide word, show instruction
      if (cardWordEl) {
        cardWordEl.innerHTML = `<strong>🎧 ${STUDY_CFG.labels.listen_and_type}</strong>`;
      }

      // Hide phonetic initially
      if (cardPhoneticEl) {
        cardPhoneticEl.style.display = "none";
      }

      // Set dictation mode class for proper centering and layout
      if (optionsArea) {
        optionsArea.className = "options-area dictation-mode";
      }

      // Add dictation layout class to flashcard container for proper spacing
      const flashcardContainer = document.getElementById("cardBox");
      if (flashcardContainer) {
        flashcardContainer.classList.add("dictation-layout");
      }

      // Auto-play audio once when dictation question loads
      if (q.audio_url) {
        setTimeout(() => {
          const audio = new Audio(q.audio_url);
          audio.play().catch((err) => console.log("Auto-play failed:", err));
        }, 1000); // Delay 1 second to let user read the instruction
      }

      // Create dictation container with proper classes
      const dictationContainer = document.createElement("div");
      dictationContainer.className = "dictation-container";

      // Add replay audio button for dictation mode
      if (q.audio_url) {
        const replayButton = document.createElement("button");
        replayButton.innerHTML = `<i class="fas fa-redo"></i> ${STUDY_CFG.labels.replay_audio}`;
        replayButton.className = "replay-audio-btn";
        replayButton.addEventListener("click", () => {
          const audio = new Audio(q.audio_url);
          audio.play().catch((err) => console.log("Audio replay failed:", err));
        });
        dictationContainer.appendChild(replayButton);
      }

      const inputRow = document.createElement("div");
      inputRow.className = "dictation-input-row";

      const inp = document.createElement("input");
      inp.type = "text";
      inp.placeholder = STUDY_CFG.labels.type_what_you_hear;
      inp.className = "type-input";

      const btn = document.createElement("button");
      btn.textContent = STUDY_CFG.labels.check;
      btn.className = "check-btn";

      btn.addEventListener("click", () => {
        if (!btn.disabled) {
          const userAnswer = inp.value.trim();
          const correct = userAnswer.toLowerCase() === q.answer.toLowerCase();
          submitAnswer(correct, userAnswer, q.answer);
        }
      });

      inp.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          if (!btn.disabled) btn.click();
        }
      });

      inputRow.appendChild(inp);
      inputRow.appendChild(btn);
      dictationContainer.appendChild(inputRow);
      optionsArea.appendChild(dictationContainer);
      setTimeout(() => inp.focus(), 100);
    } else {
      // Type answer mode - show definitions, hide word initially
      if (cardDefsEl && q.definitions && q.definitions.length > 0) {
        let defsText = "";
        q.definitions.forEach((def) => {
          if (def.english_definition) {
            defsText += `${def.english_definition}\n`;
          }
          if (def.vietnamese_definition) {
            defsText += `${def.vietnamese_definition}\n`;
          }
          defsText += "\n";
        });
        cardDefsEl.textContent = defsText.trim();
        cardDefsEl.className = "card-definitions show";
      }

      // Set options area to input mode for proper centering
      if (optionsArea) {
        optionsArea.className = "options-area input-mode";
      }

      // Hide phonetic initially
      if (cardPhoneticEl) {
        cardPhoneticEl.style.display = "none";
      }

      // Create horizontal input row container
      const inputRow = document.createElement("div");
      inputRow.className = "input-row";

      const inp = document.createElement("input");
      inp.type = "text";
      inp.placeholder = STUDY_CFG.labels.placeholder;
      inp.className = "type-input";

      const btn = document.createElement("button");
      btn.textContent = STUDY_CFG.labels.check;
      btn.className = "check-btn";

      btn.addEventListener("click", () => {
        if (!btn.disabled) {
          const userAnswer = inp.value.trim();
          const correct = userAnswer.toLowerCase() === q.answer.toLowerCase();
          submitAnswer(correct, userAnswer, q.answer);
        }
      });

      inp.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          if (!btn.disabled) btn.click();
        }
      });

      inputRow.appendChild(inp);
      inputRow.appendChild(btn);
      optionsArea.appendChild(inputRow);
      setTimeout(() => inp.focus(), 100);
    }

    // Show the answer section for user interaction
    if (answerArea) {
      answerArea.className = "answer-section active";
    }

    // Hide definitions initially only for MC mode - input mode shows them before answering
    if (q.type === "mc" && cardDefsEl) {
      cardDefsEl.className = "card-definitions";
    }
  }

  function submitAnswer(correct, userAnswer = null, expectedAnswer = null) {
    console.log(`[DEBUG] ========== SUBMIT ANSWER DEBUG START ==========`);
    console.log(`[DEBUG] Question Type: ${currentQuestion?.type}`);
    console.log(`[DEBUG] Answer Correct: ${correct}`);
    console.log(`[DEBUG] User Answer: ${userAnswer}`);
    console.log(`[DEBUG] Expected Answer: ${expectedAnswer}`);
    console.log(`[DEBUG] Current Question:`, currentQuestion);

    // Debug DOM elements state
    console.log(`[DEBUG] DOM Elements Check:`);
    console.log(`  - favoriteButton exists: ${!!favoriteButton}`);
    console.log(`  - favoriteButton parentNode: ${favoriteButton?.parentNode}`);
    console.log(`  - favoriteButton in DOM: ${document.contains(favoriteButton)}`);
    console.log(`  - cardWordEl exists: ${!!cardWordEl}`);
    console.log(`  - optionsArea exists: ${!!optionsArea}`);

    // Store the actual correctness for later use in submitGrade
    window.currentAnswerCorrectness = correct;

    // Clear any existing timeout
    if (nextTimeout) {
      clearTimeout(nextTimeout);
      nextTimeout = null;
    }

    // Play audio feedback immediately
    if (correct) {
      AudioFeedback.playCorrect();
      console.log(`[DEBUG] Playing correct audio feedback`);
    } else {
      AudioFeedback.playIncorrect();
      console.log(`[DEBUG] Playing incorrect audio feedback`);
    }

    // Hide answer elements based on question type
    if (currentQuestion.type === "mc") {
      // Multiple choice: hide all option buttons
      const optionButtons = optionsArea.querySelectorAll(".option-btn");
      optionButtons.forEach((btn) => {
        btn.classList.add("hidden");
        btn.style.display = "none";
      });
    } else if (currentQuestion.type === "dictation") {
      // Dictation mode: hide replay button, input field, and check button
      const replayBtn = optionsArea.querySelector(".replay-audio-btn");
      const inputField = optionsArea.querySelector(".type-input");
      const checkBtn = optionsArea.querySelector(".check-btn");

      if (replayBtn) {
        replayBtn.classList.add("hidden");
        replayBtn.style.display = "none";
      }
      if (inputField) {
        inputField.classList.add("hidden");
        inputField.style.display = "none";
      }
      if (checkBtn) {
        checkBtn.classList.add("hidden");
        checkBtn.style.display = "none";
      }
    } else {
      // Input mode: hide the entire input row (input field and check button)
      const inputRow = optionsArea.querySelector(".input-row");
      if (inputRow) {
        inputRow.classList.add("hidden");

        // Fallback: Force hide with inline styles if CSS doesn't work
        inputRow.style.display = "none";
        inputRow.style.visibility = "hidden";
        inputRow.style.opacity = "0";
        inputRow.style.height = "0";
        inputRow.style.overflow = "hidden";
      }
    }

    // Update stats
    if (correct) {
      correctCnt++;
    } else {
      incorrectCnt++;
    }
    updateStats();

    // Show detailed feedback for input modes
    if ((currentQuestion.type === "type" || currentQuestion.type === "dictation") && 
        userAnswer !== null && expectedAnswer !== null) {
      showDetailedInputFeedback(correct, userAnswer, expectedAnswer);
    }

    // Remove feedbackMsg text
    if (feedbackMsg) {
      feedbackMsg.textContent = "";
      feedbackMsg.className = "feedback-message";
    }
    // Border color feedback
    const flashcardContainer = document.getElementById("cardBox");
    if (flashcardContainer) {
      flashcardContainer.classList.remove(
        "flashcard-correct",
        "flashcard-incorrect"
      );
      if (correct) {
        flashcardContainer.classList.add("flashcard-correct");
      } else {
        flashcardContainer.classList.add("flashcard-incorrect");
      }
    }

    // NOW reveal the correct answer and make word clickable for Cambridge Dictionary with fallback
    if (cardWordEl && currentQuestion.word) {
      // Check if DictionaryUtils is available
      if (typeof window.DictionaryUtils !== "undefined") {
        // Use the new fallback mechanism
        const wordLink = DictionaryUtils.createDictionaryLink(
          currentQuestion.word,
          {
            className: "word-link",
            text: currentQuestion.word,
            onFallback: (word, fallbackUrl) => {
              console.log(
                `Study: Using fallback dictionary URL for ${word}: ${fallbackUrl}`
              );
            },
            onError: (error) => {
              console.error(
                `Study: Dictionary fallback failed for ${currentQuestion.word}:`,
                error
              );
            },
          }
        );

        // Wrap in strong tag and set as innerHTML
        const strongElement = document.createElement("strong");
        strongElement.appendChild(wordLink);
        
        // Add part of speech if available
        if (currentQuestion.part_of_speech) {
          const posSpan = document.createElement("span");
          const abbreviatedPos = abbreviatePartOfSpeech(currentQuestion.part_of_speech);
          posSpan.textContent = ` (${abbreviatedPos})`;
          posSpan.style.fontStyle = "italic";
          posSpan.style.color = "var(--primary-color)";
          posSpan.style.fontWeight = "normal";
          posSpan.style.fontSize = "0.7em";
          strongElement.appendChild(posSpan);
        }
        
        cardWordEl.innerHTML = "";
        cardWordEl.appendChild(strongElement);

        console.log(
          "Clickable word created with fallback mechanism:",
          currentQuestion.word
        );
      } else {
        // Fallback to original implementation if DictionaryUtils is not available
        console.warn(
          "DictionaryUtils not available, using direct Cambridge Dictionary link"
        );
        const cambridgeUrl = `https://dictionary.cambridge.org/dictionary/english/${encodeURIComponent(
          currentQuestion.word
        )}`;
        
        // Create word with part of speech
        let wordDisplay = currentQuestion.word;
        if (currentQuestion.part_of_speech) {
          const abbreviatedPos = abbreviatePartOfSpeech(currentQuestion.part_of_speech);
          wordDisplay += ` <span style="font-style: italic; color: var(--primary-color); font-weight: normal; font-size: 0.7em;">(${abbreviatedPos})</span>`;
        }
        
        cardWordEl.innerHTML = `<a href="${cambridgeUrl}" target="_blank" class="word-link"><strong>${wordDisplay}</strong></a>`;
        console.log(
          "Clickable word created (fallback):",
          currentQuestion.word,
          "URL:",
          cambridgeUrl
        );
      }
    } else {
      console.log(
        "Cannot create clickable word - cardWordEl:",
        !!cardWordEl,
        "word:",
        currentQuestion.word
      );
    }

    // Show phonetic if available
    if (cardPhoneticEl && currentQuestion.phonetic) {
      cardPhoneticEl.textContent = `/${currentQuestion.phonetic}/`;
      cardPhoneticEl.style.display = "block";
    }

    // Show and setup favorite button
    let currentFavoriteButton = favoriteButton;

    // Re-query the favorite button if the original reference is stale
    if (!currentFavoriteButton || !document.contains(currentFavoriteButton)) {
      console.warn(`[WARN] Favorite button reference is stale, re-querying...`);
      currentFavoriteButton = document.getElementById("favoriteButton");
    }

    if (currentFavoriteButton && currentQuestion.id) {
      currentFavoriteButton.style.display = "block";
      currentFavoriteButton.setAttribute("data-card-id", currentQuestion.id);

      // To prevent stale event listeners, clone and replace the button.
      // This is safer than trying to remove specific listeners.
      // It also avoids race conditions where the button's state is cloned before being updated.
      let newFavoriteButton = currentFavoriteButton;
      if (currentFavoriteButton.parentNode) {
        newFavoriteButton = currentFavoriteButton.cloneNode(true);
        currentFavoriteButton.parentNode.replaceChild(newFavoriteButton, currentFavoriteButton);
      }
      
      // Add the event listener to the new, clean button.
      newFavoriteButton.addEventListener("click", handleStudyFavoriteToggle);

      // Now, load the favorite status for the current card.
      // This will fetch the status and update the new button's appearance.
      loadCardFavoriteStatus(currentQuestion.id);
    } else {
      console.log(`[DEBUG] Favorite button setup skipped - button exists: ${!!currentFavoriteButton}, question ID: ${currentQuestion?.id}`);
    }

    // Show definitions in the definitions area
    if (cardDefsEl && currentQuestion.definitions) {
      let defsText = "";
      
      currentQuestion.definitions.forEach((def) => {
        if (def.english_definition) {
          defsText += `${def.english_definition}\n`;
        }
        if (def.vietnamese_definition) {
          defsText += `${def.vietnamese_definition}\n`;
        }
        defsText += "\n";
      });
      cardDefsEl.textContent = defsText.trim();
      cardDefsEl.className = "card-definitions show";
    }

    // NOW show audio button after answer submission
    if (audioButton && currentQuestion.audio_url) {
      audioButton.style.display = "block";
      audioButton.onclick = () => {
        const audio = new Audio(currentQuestion.audio_url);
        audio.play().catch((err) => console.log("Audio play failed:", err));
      };
    }
    
    // Show recording controls after answer submission
    const recordingControls = document.querySelector('.recording-controls');
    if (recordingControls) {
      recordingControls.style.display = 'flex';
      VoiceRecording.clearRecording(); // Clear previous recording data
    }

    // Auto-play audio after revealing answer
    if (currentQuestion.audio_url) {
      setTimeout(() => {
        const audio = new Audio(currentQuestion.audio_url);
        audio.play().catch((err) => console.log("Auto-play failed:", err));
      }, 500); // Delay 500ms to let user see the answer first
    }

    // Show grade buttons
    console.log(`[DEBUG] Attempting to show grade buttons...`);
    const gradeButtons = document.getElementById("gradeButtons");
    console.log(`[DEBUG] Grade buttons element found:`, !!gradeButtons);

    if (gradeButtons) {
      // Remove any hidden classes and add show class
      gradeButtons.classList.remove("hidden");
      gradeButtons.classList.add("show");

      // Ensure the element has the correct base class
      if (!gradeButtons.classList.contains("grade-buttons")) {
        gradeButtons.classList.add("grade-buttons");
      }

      // Force display using inline style as backup (CSS should handle this with .grade-buttons.show)
      gradeButtons.style.display = "grid";
      gradeButtons.style.visibility = "visible";

      console.log(`[DEBUG] Grade buttons should now be visible`);
      console.log(`[DEBUG] Grade buttons classes:`, gradeButtons.className);
      console.log(`[DEBUG] Grade buttons display style:`, gradeButtons.style.display);
      console.log(`[DEBUG] Grade buttons visibility:`, gradeButtons.style.visibility);

      // Additional debugging - check computed styles
      const computedStyle = window.getComputedStyle(gradeButtons);
      console.log(`[DEBUG] Computed display:`, computedStyle.display);
      console.log(`[DEBUG] Computed visibility:`, computedStyle.visibility);
    } else {
      console.error(`[ERROR] Grade buttons element not found! Cannot show difficulty rating.`);
    }

    // Handle grade button clicks - only attach listeners if not already attached
    const gradeBtns = document.querySelectorAll(".grade-btn");
    console.log(`[DEBUG] Found ${gradeBtns.length} grade button elements`);

    gradeBtns.forEach((btn, index) => {
      console.log(`[DEBUG] Grade button ${index + 1}: grade=${btn.dataset.grade}, hasListener=${btn.hasAttribute("data-listener-attached")}`);

      // Check if listener is already attached
      if (!btn.hasAttribute("data-listener-attached")) {
        btn.setAttribute("data-listener-attached", "true");
        btn.onclick = () => {
          const grade = parseInt(btn.dataset.grade);
          console.log(`[DEBUG] Grade button clicked: ${grade}`);
          submitGrade(grade);
        };
        console.log(`[DEBUG] Attached click listener to grade button ${index + 1}`);
      }
    });

    console.log(`[DEBUG] ========== SUBMIT ANSWER DEBUG END ==========`);
  }

  function submitGrade(grade) {
    console.log(`[DEBUG] ========== SUBMIT GRADE DEBUG START ==========`);
    console.log(`[DEBUG] Grade submitted: ${grade}`);
    console.log(`[DEBUG] Question Type: ${currentQuestion?.type}`);
    console.log(`[DEBUG] Current Answer Correctness: ${window.currentAnswerCorrectness}`);

    // Prevent multiple submissions for the same question
    if (window.submittingGrade) {
      console.log(
        "[DEBUG] Grade submission already in progress, ignoring duplicate call"
      );
      return;
    }

    // Check if we have a current question to submit for
    if (!currentQuestion || !currentQuestion.id) {
      console.log("[DEBUG] No current question to submit grade for");
      return;
    }

    window.submittingGrade = true;
    console.log(`[DEBUG] Starting grade submission process...`);

    // Calculate response time
    const responseTime = questionStartTime
      ? (Date.now() - questionStartTime) / 1000
      : 0;

    // Use the actual answer correctness, not the grade
    const actualCorrectness =
      window.currentAnswerCorrectness !== undefined
        ? window.currentAnswerCorrectness
        : grade >= 2;

    fetch(STUDY_CFG.submitUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": STUDY_CFG.csrfToken,
      },
      body: JSON.stringify({
        card_id: currentQuestion.id,
        correct: actualCorrectness, // Use actual answer correctness, not grade-based
        response_time: responseTime,
        question_type: currentQuestion.type || "multiple_choice",
        grade: grade, // Also send the grade for spaced repetition algorithm
      }),
    })
      .then((r) => {
        if (!r.ok) {
          throw new Error(`HTTP ${r.status}: ${r.statusText}`);
        }
        return r.json();
      })
      .then((data) => {
        if (data.success) {
          // Reset submission flag and proceed to next question
          window.submittingGrade = false;
          getNextQuestion();
        } else {
          console.error(
            "Grade submission failed:",
            data.error || "Unknown error"
          );
          // Reset submission flag and still proceed to next question to avoid getting stuck
          window.submittingGrade = false;
          getNextQuestion();
        }
      })
      .catch((error) => {
        console.error("Error submitting grade:", error);
        // Reset submission flag and still proceed to next question to avoid getting stuck
        window.submittingGrade = false;
        getNextQuestion();
      });
  }

  // Mode Slider Class
  class ModeSlider {
    constructor() {
      console.log("🎯 Initializing ModeSlider...");
      this.currentSlide = 0;
      this.totalSlides = modeSlides.length;
      console.log(`📊 Found ${this.totalSlides} mode slides:`, modeSlides);
      this.isTransitioning = false;
      this.touchStartX = 0;
      this.touchEndX = 0;
      this.isEnabled = false; // Start as disabled, will be enabled in init()

      // Store bound event handlers for removal
      this.boundPrevSlide = () => this.prevSlide();
      this.boundNextSlide = () => this.nextSlide();
      this.boundKeydownHandler = (e) => this.handleKeydown(e);
      this.boundTouchStart = (e) => this.handleTouchStart(e);
      this.boundTouchEnd = (e) => this.handleTouchEnd(e);
      this.boundTouchMove = (e) => e.preventDefault();

      this.init();
    }

    init() {
      // Set initial state
      this.updateSlider();
      this.updateIndicators();
      this.updateNavButtons();

      this.enableEventListeners();
    }

    enableEventListeners() {
      if (!this.isEnabled) {
        this.isEnabled = true;

        console.log("🎯 ModeSlider: Enabling event listeners...");

        // Add arrow button event listeners
        if (sliderPrev) {
          sliderPrev.addEventListener("click", this.boundPrevSlide);
          console.log("✅ Added click listener to sliderPrev");
        } else {
          console.warn("❌ sliderPrev element not found");
        }

        if (sliderNext) {
          sliderNext.addEventListener("click", this.boundNextSlide);
          console.log("✅ Added click listener to sliderNext");
        } else {
          console.warn("❌ sliderNext element not found");
        }

        // Store indicator handlers for removal
        this.indicatorHandlers = [];

        // Indicator clicks
        indicators.forEach((indicator, index) => {
          const handler = () => this.goToSlide(index);
          this.indicatorHandlers.push({ indicator, handler });
          indicator.addEventListener("click", handler);
        });
        console.log(
          `✅ Added click listeners to ${indicators.length} indicators`
        );

        // Touch/swipe support
        if (modeSlider) {
          modeSlider.addEventListener("touchstart", this.boundTouchStart);
          modeSlider.addEventListener("touchend", this.boundTouchEnd);
          modeSlider.addEventListener("touchmove", this.boundTouchMove);
          console.log("✅ Added touch/swipe listeners");
        }

        // Keyboard navigation
        document.addEventListener("keydown", this.boundKeydownHandler);
        console.log("✅ Added keyboard navigation listener");

        console.log("🎯 ModeSlider: Event listeners enabled successfully");
      } else {
        console.log("⚠️ ModeSlider: Event listeners already enabled, skipping");
      }
    }

    disableEventListeners() {
      if (this.isEnabled) {
        this.isEnabled = false;

        // Remove arrow button event listeners
        if (sliderPrev) {
          sliderPrev.removeEventListener("click", this.boundPrevSlide);
        }

        if (sliderNext) {
          sliderNext.removeEventListener("click", this.boundNextSlide);
        }

        // Remove indicator clicks
        if (this.indicatorHandlers) {
          this.indicatorHandlers.forEach(({ indicator, handler }) => {
            indicator.removeEventListener("click", handler);
          });
          this.indicatorHandlers = [];
        }

        // Remove touch/swipe support
        if (modeSlider) {
          modeSlider.removeEventListener("touchstart", this.boundTouchStart);
          modeSlider.removeEventListener("touchend", this.boundTouchEnd);
          modeSlider.removeEventListener("touchmove", this.boundTouchMove);
        }

        // Remove keyboard navigation
        document.removeEventListener("keydown", this.boundKeydownHandler);

        console.log("ModeSlider: Event listeners disabled");
      }
    }

    handleKeydown(e) {
      if (!this.isEnabled) return;

      if (e.key === "ArrowLeft") this.prevSlide();
      if (e.key === "ArrowRight") this.nextSlide();
    }

    updateSlider() {
      if (!modeSlider) return;

      const translateX = -this.currentSlide * 100;
      modeSlider.style.transform = `translateX(${translateX}%)`;

      // Update active slide
      modeSlides.forEach((slide, index) => {
        slide.classList.toggle("active", index === this.currentSlide);
      });

      // Trigger radio button change
      const activeSlide = modeSlides[this.currentSlide];
      if (activeSlide) {
        const radio = activeSlide.querySelector('input[type="radio"]');
        if (radio) {
          radio.checked = true;
          handleStudyModeChange();
        }
      }
    }

    updateIndicators() {
      indicators.forEach((indicator, index) => {
        indicator.classList.toggle("active", index === this.currentSlide);
      });
    }

    updateNavButtons() {
      if (sliderPrev) {
        sliderPrev.disabled = this.currentSlide === 0;
      }
      if (sliderNext) {
        sliderNext.disabled = this.currentSlide === this.totalSlides - 1;
      }
    }

    goToSlide(index) {
      console.log(
        `🎯 goToSlide(${index}) called, current: ${this.currentSlide}, enabled: ${this.isEnabled}, transitioning: ${this.isTransitioning}`
      );

      if (!this.isEnabled) {
        console.warn("⚠️ goToSlide() blocked - slider disabled");
        return;
      }

      if (this.isTransitioning) {
        console.warn("⚠️ goToSlide() blocked - transition in progress");
        return;
      }

      if (index === this.currentSlide) {
        console.log("⚠️ goToSlide() blocked - already at target slide");
        return;
      }

      this.isTransitioning = true;
      this.currentSlide = Math.max(0, Math.min(index, this.totalSlides - 1));

      console.log(`🎯 Transitioning to slide ${this.currentSlide}`);
      this.updateSlider();
      this.updateIndicators();
      this.updateNavButtons();

      setTimeout(() => {
        this.isTransitioning = false;
        console.log("✅ Transition completed");
      }, 400);
    }

    nextSlide() {
      console.log("🎯 nextSlide() called, isEnabled:", this.isEnabled);
      if (!this.isEnabled) {
        console.warn("⚠️ nextSlide() blocked - slider disabled");
        return;
      }

      if (this.currentSlide < this.totalSlides - 1) {
        console.log(`➡️ Moving to slide ${this.currentSlide + 1}`);
        this.goToSlide(this.currentSlide + 1);
      } else {
        console.log("➡️ Already at last slide");
      }
    }

    prevSlide() {
      console.log("🎯 prevSlide() called, isEnabled:", this.isEnabled);
      if (!this.isEnabled) {
        console.warn("⚠️ prevSlide() blocked - slider disabled");
        return;
      }

      if (this.currentSlide > 0) {
        console.log(`⬅️ Moving to slide ${this.currentSlide - 1}`);
        this.goToSlide(this.currentSlide - 1);
      } else {
        console.log("⬅️ Already at first slide");
      }
    }

    handleTouchStart(e) {
      this.touchStartX = e.touches[0].clientX;
    }

    handleTouchEnd(e) {
      this.touchEndX = e.changedTouches[0].clientX;
      this.handleSwipe();
    }

    handleSwipe() {
      const swipeThreshold = 50;
      const diff = this.touchStartX - this.touchEndX;

      if (Math.abs(diff) > swipeThreshold) {
        if (diff > 0) {
          this.nextSlide();
        } else {
          this.prevSlide();
        }
      }
    }
  }

  // Initialize slider
  let modeSliderInstance;
  if (modeSlider) {
    console.log("🎯 Initializing ModeSlider...");
    console.log("🔍 Found elements:", {
      modeSlider: !!modeSlider,
      sliderPrev: !!sliderPrev,
      sliderNext: !!sliderNext,
      indicators: indicators.length,
      modeSlides: modeSlides.length,
    });
    modeSliderInstance = new ModeSlider();
    console.log("✅ ModeSlider initialized successfully");

    // Test arrow button functionality after a short delay
    setTimeout(() => {
      console.log("🧪 Testing arrow button functionality...");
      if (sliderPrev && sliderNext) {
        console.log("🔍 Arrow button states:", {
          prevDisabled: sliderPrev.disabled,
          nextDisabled: sliderNext.disabled,
          prevHasListeners:
            sliderPrev.onclick !== null ||
            sliderPrev.addEventListener !== undefined,
          nextHasListeners:
            sliderNext.onclick !== null ||
            sliderNext.addEventListener !== undefined,
        });
      }
    }, 100);
  } else {
    console.warn("❌ modeSlider element not found - slider not initialized");
  }

  // Study mode selection handling
  function handleStudyModeChange() {
    const selectedMode = document.querySelector(
      'input[name="study_mode"]:checked'
    ).value;
    currentStudyMode = selectedMode;

    if (selectedMode === "decks") {
      deckStudyOptions.classList.remove("hidden");
      randomStudyOptions.classList.add("hidden");
      if (reviewStudyOptions) reviewStudyOptions.classList.add("hidden");
    } else if (selectedMode === "review") {
      deckStudyOptions.classList.add("hidden");
      randomStudyOptions.classList.add("hidden");
      if (reviewStudyOptions) reviewStudyOptions.classList.remove("hidden");
    } else if (selectedMode === "favorites") {
      deckStudyOptions.classList.add("hidden");
      randomStudyOptions.classList.add("hidden");
      if (reviewStudyOptions) reviewStudyOptions.classList.add("hidden");
    } else {
      deckStudyOptions.classList.add("hidden");
      randomStudyOptions.classList.remove("hidden");
      if (reviewStudyOptions) reviewStudyOptions.classList.add("hidden");
    }
  }

  // Initialize study mode selection
  studyModeRadios.forEach((radio) => {
    radio.addEventListener("change", handleStudyModeChange);
  });

  // Handle random word count input
  if (randomWordCountInput) {
    randomWordCountInput.addEventListener("input", (e) => {
      wordCount = parseInt(e.target.value) || 10;
    });
  }

  // Handle start buttons
  if (startBtnDecks) {
    startBtnDecks.addEventListener("click", () => {
      if (currentStudyMode === "decks") {
        const selectedDeckIds = Array.from(
          document.querySelectorAll('input[name="deck_ids"]:checked')
        ).map((cb) => cb.value);
        if (selectedDeckIds.length === 0) {
          alert(
            STUDY_CFG.labels.select_deck_alert ||
              "Please select at least one deck to study."
          );
          return;
        }

        // Store selected deck IDs
        deckIds = selectedDeckIds;
      } else if (currentStudyMode === "review") {
        // Check if there are incorrect words to review
        if (
          !reviewModeOption ||
          reviewModeOption.classList.contains("disabled")
        ) {
          alert(
            "No incorrect words to review. Answer some questions incorrectly first!"
          );
          return;
        }
      }

      // Reset session data
      correctCnt = 0;
      incorrectCnt = 0;
      seenCardIds = [];
      updateStats();

      // Hide all selection areas and show study area
      const studyModeSection = document.querySelector(".study-mode-section");
      if (studyModeSection) studyModeSection.style.display = "none";
      if (deckStudyOptions) deckStudyOptions.classList.add("hidden");
      if (randomStudyOptions) randomStudyOptions.classList.add("hidden");
      if (reviewStudyOptions) reviewStudyOptions.classList.add("hidden");
      if (studyArea) {
        studyArea.style.display = "block";
        studyArea.className = "study-area active";
      }
      if (studyHeader) studyHeader.style.display = "none";

      // Disable mode slider navigation during study session
      if (modeSliderInstance) {
        modeSliderInstance.disableEventListeners();
      }

      // Start the study session timer
      startStudyTimer();

      // Start studying
      getNextQuestion();
    });
  }

  if (startBtnRandom) {
    startBtnRandom.addEventListener("click", () => {
      // Reset session data
      correctCnt = 0;
      incorrectCnt = 0;
      seenCardIds = [];
      updateStats();

      // Hide all selection areas and show study area
      const studyModeSection = document.querySelector(".study-mode-section");
      if (studyModeSection) studyModeSection.style.display = "none";
      if (deckStudyOptions) deckStudyOptions.classList.add("hidden");
      if (randomStudyOptions) randomStudyOptions.classList.add("hidden");
      if (reviewStudyOptions) reviewStudyOptions.classList.add("hidden");
      if (studyArea) {
        studyArea.style.display = "block";
        studyArea.className = "study-area active";
      }
      if (studyHeader) studyHeader.style.display = "none";

      // Disable mode slider navigation during study session
      if (modeSliderInstance) {
        modeSliderInstance.disableEventListeners();
      }

      // Start the study session timer
      startStudyTimer();

      // Start studying
      getNextQuestion();
    });
  }

  if (startBtnReview) {
    startBtnReview.addEventListener("click", () => {
      // Check if there are incorrect words to review
      if (startBtnReview.disabled) {
        alert(
          "No incorrect words to review. Answer some questions incorrectly first!"
        );
        return;
      }

      // Reset session data
      correctCnt = 0;
      incorrectCnt = 0;
      seenCardIds = [];
      updateStats();

      // Hide all selection areas and show study area
      const studyModeSection = document.querySelector(".study-mode-section");
      if (studyModeSection) studyModeSection.style.display = "none";
      if (deckStudyOptions) deckStudyOptions.classList.add("hidden");
      if (randomStudyOptions) randomStudyOptions.classList.add("hidden");
      if (reviewStudyOptions) reviewStudyOptions.classList.add("hidden");
      if (studyArea) {
        studyArea.style.display = "block";
        studyArea.className = "study-area active";
      }
      if (studyHeader) studyHeader.style.display = "none";

      // Disable mode slider navigation during study session
      if (modeSliderInstance) {
        modeSliderInstance.disableEventListeners();
      }

      // Start the study session timer
      startStudyTimer();

      // Start studying
      getNextQuestion();
    });
  }

  // Back button handling
  if (backBtn) {
    backBtn.addEventListener("click", () => {
      // Hide study area
      studyArea.style.display = "none";

      // Reset study area content
      if (cardWordEl) cardWordEl.innerHTML = "";
      if (cardPhoneticEl) cardPhoneticEl.style.display = "none";
      if (cardImageEl) cardImageEl.style.display = "none";
      if (cardDefsEl) cardDefsEl.innerHTML = "";
      if (optionsArea) optionsArea.innerHTML = "";
      if (feedbackMsg) feedbackMsg.style.display = "none";

      const gradeButtons = document.getElementById("gradeButtons");
      if (gradeButtons) {
        gradeButtons.className = "grade-buttons"; // Remove 'show' class to hide
        gradeButtons.classList.remove("show", "hidden"); // Clean up any extra classes
        gradeButtons.style.display = ""; // Clear inline styles to let CSS take over
        gradeButtons.style.visibility = ""; // Clear inline visibility
      }

      const noCardMsg = document.getElementById("noCardMsg");
      if (noCardMsg) noCardMsg.className = "no-cards-message";

      // Show study mode selection again
      const studyModeSection = document.querySelector(".study-mode-section");
      if (studyModeSection) studyModeSection.style.display = "block";

      // Re-enable mode slider navigation when returning to study selection
      if (modeSliderInstance) {
        modeSliderInstance.enableEventListeners();
      }

      // Show appropriate options based on current mode
      if (currentStudyMode === "decks") {
        if (deckStudyOptions) deckStudyOptions.classList.remove("hidden");
        if (randomStudyOptions) randomStudyOptions.classList.add("hidden");
        if (reviewStudyOptions) reviewStudyOptions.classList.add("hidden");
      } else if (currentStudyMode === "review") {
        if (deckStudyOptions) deckStudyOptions.classList.add("hidden");
        if (randomStudyOptions) randomStudyOptions.classList.add("hidden");
        if (reviewStudyOptions) reviewStudyOptions.classList.remove("hidden");
      } else {
        if (deckStudyOptions) deckStudyOptions.classList.add("hidden");
        if (randomStudyOptions) randomStudyOptions.classList.remove("hidden");
        if (reviewStudyOptions) reviewStudyOptions.classList.add("hidden");
      }

      // Reset study session timer
      resetStudyTimer();

      // Reset stats
      correctCnt = 0;
      incorrectCnt = 0;
      updateStats();
      if (studyHeader) studyHeader.style.display = "";

      // Refresh incorrect words count when returning to study selection
      loadIncorrectWordsCount();
    });
  }

  // Initialize deck selector popup functionality
  const deckModal = document.getElementById("deckSelectorModal");
  const openDeckSelector = document.getElementById("openDeckSelector");
  const closeDeckModal = document.getElementById("closeDeckModal");
  const cancelDeckSelection = document.getElementById("cancelDeckSelection");
  const confirmDeckSelection = document.getElementById("confirmDeckSelection");
  const selectedDecksPreview = document.getElementById("selectedDecksPreview");
  
  const deckGrid = document.getElementById("deckGrid");
  const deckSearchInput = document.getElementById("deckSearchInput");
  const selectAllDecks = document.getElementById("selectAllDecks");
  const deselectAllDecks = document.getElementById("deselectAllDecks");
  const selectedCount = document.getElementById("selectedCount");
  const deckCheckboxes = document.querySelectorAll('.deck-checkbox');
  const deckCards = document.querySelectorAll('.deck-card');

  let tempSelectedDecks = []; // Store temporary selections
  let lastClickedDeckIndex = -1; // Track last clicked deck for range selection

  // Update selected count and card styling
  function updateDeckSelection() {
    const selectedDecks = Array.from(deckCheckboxes).filter(cb => cb.checked);
    const count = selectedDecks.length;
    
    if (selectedCount) {
      selectedCount.textContent = count;
    }
    
    // Update card styling
    deckCards.forEach(card => {
      const checkbox = card.querySelector('.deck-checkbox');
      if (checkbox && checkbox.checked) {
        card.classList.add('selected');
      } else {
        card.classList.remove('selected');
      }
    });
  }

  // Update preview text in main button
  function updatePreviewText() {
    const selectedDecks = Array.from(deckCheckboxes).filter(cb => cb.checked);
    const count = selectedDecks.length;
    
    if (count === 0) {
      selectedDecksPreview.textContent = STUDY_CFG.labels.no_decks_selected || "No decks selected";
    } else if (count === 1) {
      const deckName = selectedDecks[0].closest('.deck-card').querySelector('.deck-name').textContent;
      selectedDecksPreview.textContent = deckName;
    } else {
      selectedDecksPreview.textContent = `${count} decks selected`;
    }
  }

  // Search/filter functionality
  function filterDecks(searchTerm) {
    const term = searchTerm.toLowerCase().trim();
    deckCards.forEach(card => {
      const deckName = card.dataset.deckName || '';
      if (deckName.includes(term)) {
        card.style.display = 'block';
      } else {
        card.style.display = 'none';
      }
    });
  }

  // Get visible deck cards (not hidden by filter)
  function getVisibleDeckCards() {
    return Array.from(deckCards).filter(card => 
      card.style.display !== 'none' && 
      getComputedStyle(card).display !== 'none'
    );
  }

  // Handle range selection with Ctrl+Click
  function handleRangeSelection(clickedIndex, isCtrlHeld) {
    console.log('handleRangeSelection called:', { clickedIndex, isCtrlHeld, lastClickedDeckIndex });
    
    if (!isCtrlHeld || lastClickedDeckIndex === -1) {
      lastClickedDeckIndex = clickedIndex;
      return;
    }

    const visibleCards = getVisibleDeckCards();
    console.log('visibleCards:', visibleCards.length);
    
    const startIndex = Math.min(lastClickedDeckIndex, clickedIndex);
    const endIndex = Math.max(lastClickedDeckIndex, clickedIndex);
    console.log('Range:', { startIndex, endIndex });
    
    // Determine the selection state - toggle based on the clicked card's CURRENT state
    const clickedCard = visibleCards[clickedIndex];
    const clickedCheckbox = clickedCard.querySelector('.deck-checkbox');
    const targetState = !clickedCheckbox.checked; // Toggle the clicked card's state
    
    console.log('Target state:', targetState);

    // Apply the same state to all cards in the range
    for (let i = startIndex; i <= endIndex; i++) {
      const card = visibleCards[i];
      if (card) {
        const checkbox = card.querySelector('.deck-checkbox');
        if (checkbox) {
          checkbox.checked = targetState;
          console.log(`Set card ${i} to:`, targetState);
        }
      }
    }

    updateDeckSelection();
    lastClickedDeckIndex = clickedIndex;
  }

  // Save current selections as temporary
  function saveTempSelections() {
    tempSelectedDecks = Array.from(deckCheckboxes)
      .filter(cb => cb.checked)
      .map(cb => cb.value);
  }

  // Restore temporary selections
  function restoreTempSelections() {
    deckCheckboxes.forEach(checkbox => {
      checkbox.checked = tempSelectedDecks.includes(checkbox.value);
    });
    updateDeckSelection();
  }

  // Apply selections permanently
  function applySelections() {
    saveTempSelections();
    updatePreviewText();
  }

  // Open modal
  function openModal() {
    saveTempSelections(); // Save current state
    deckModal.classList.add('show');
    document.body.style.overflow = 'hidden';
    
    // Focus search input
    setTimeout(() => {
      if (deckSearchInput) deckSearchInput.focus();
    }, 100);
  }

  // Close modal
  function closeModal() {
    deckModal.classList.remove('show');
    document.body.style.overflow = '';
    restoreTempSelections(); // Restore previous state
    
    // Clear search
    if (deckSearchInput) {
      deckSearchInput.value = '';
      filterDecks('');
    }
  }

  // Confirm selections
  function confirmSelections() {
    applySelections();
    deckModal.classList.remove('show');
    document.body.style.overflow = '';
    
    // Clear search
    if (deckSearchInput) {
      deckSearchInput.value = '';
      filterDecks('');
    }
  }

  // Event listeners
  if (openDeckSelector) {
    openDeckSelector.addEventListener('click', openModal);
  }

  if (closeDeckModal) {
    closeDeckModal.addEventListener('click', closeModal);
  }

  if (cancelDeckSelection) {
    cancelDeckSelection.addEventListener('click', closeModal);
  }

  if (confirmDeckSelection) {
    confirmDeckSelection.addEventListener('click', confirmSelections);
  }

  // Close modal when clicking outside
  if (deckModal) {
    deckModal.addEventListener('click', (e) => {
      if (e.target === deckModal) {
        closeModal();
      }
    });
  }

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (deckModal && deckModal.classList.contains('show')) {
      if (e.key === 'Escape') {
        closeModal();
      } else if (e.key === 'Enter' && e.ctrlKey) {
        confirmSelections();
      }
    }
  });

  if (deckSearchInput) {
    deckSearchInput.addEventListener('input', (e) => {
      filterDecks(e.target.value);
      lastClickedDeckIndex = -1; // Reset range selection when filtering
    });
  }

  if (selectAllDecks) {
    selectAllDecks.addEventListener('click', () => {
      deckCheckboxes.forEach(checkbox => {
        const card = checkbox.closest('.deck-card');
        if (card && card.style.display !== 'none') {
          checkbox.checked = true;
        }
      });
      lastClickedDeckIndex = -1; // Reset range selection
      updateDeckSelection();
    });
  }

  if (deselectAllDecks) {
    deselectAllDecks.addEventListener('click', () => {
      deckCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
      });
      lastClickedDeckIndex = -1; // Reset range selection
      updateDeckSelection();
    });
  }

  // Visual feedback for range selection
  function updateRangeHover(hoveredIndex, isCtrlHeld) {
    // Clear all previous range hover classes
    deckCards.forEach(card => card.classList.remove('range-hover'));
    
    if (!isCtrlHeld || lastClickedDeckIndex === -1 || hoveredIndex === -1) {
      return;
    }

    const visibleCards = getVisibleDeckCards();
    const startIndex = Math.min(lastClickedDeckIndex, hoveredIndex);
    const endIndex = Math.max(lastClickedDeckIndex, hoveredIndex);
    
    // Add range hover class to cards in range
    for (let i = startIndex; i <= endIndex; i++) {
      const card = visibleCards[i];
      if (card) {
        card.classList.add('range-hover');
      }
    }
  }

  // Deck card click handling with Ctrl+Click support
  deckCards.forEach((card, index) => {
    card.addEventListener('click', (e) => {
      e.preventDefault();
      const checkbox = card.querySelector('.deck-checkbox');
      if (!checkbox) return;

      const isCtrlHeld = e.ctrlKey;
      const visibleCards = getVisibleDeckCards();
      const visibleIndex = visibleCards.indexOf(card);
      
      console.log('Card clicked:', { 
        cardIndex: index, 
        visibleIndex, 
        isCtrlHeld, 
        lastClickedDeckIndex,
        cardText: card.querySelector('.deck-name')?.textContent 
      });

      if (visibleIndex === -1) {
        console.log('Card is not visible, returning');
        return; // Card is not visible
      }

      if (isCtrlHeld && lastClickedDeckIndex !== -1) {
        console.log('Calling handleRangeSelection');
        // Handle range selection
        handleRangeSelection(visibleIndex, true);
      } else {
        console.log('Normal single click');
        // Normal single click
        checkbox.checked = !checkbox.checked;
        lastClickedDeckIndex = visibleIndex;
        updateDeckSelection();
      }
    });

    // Add hover effects for range selection preview
    card.addEventListener('mouseenter', (e) => {
      const visibleCards = getVisibleDeckCards();
      const visibleIndex = visibleCards.indexOf(card);
      updateRangeHover(visibleIndex, e.ctrlKey);
    });

    card.addEventListener('mouseleave', () => {
      card.classList.remove('range-hover');
    });
  });

  // Listen for ctrl key changes to update hover effects
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Control' && deckModal && deckModal.classList.contains('show')) {
      const hoveredCard = document.querySelector('.deck-card:hover');
      if (hoveredCard) {
        const visibleCards = getVisibleDeckCards();
        const visibleIndex = visibleCards.indexOf(hoveredCard);
        updateRangeHover(visibleIndex, true);
      }
    }
  });

  document.addEventListener('keyup', (e) => {
    if (e.key === 'Control') {
      // Clear all range hover effects
      deckCards.forEach(card => card.classList.remove('range-hover'));
    }
  });

  // Checkbox change events - prevent this from interfering with our click handling
  deckCheckboxes.forEach((checkbox, index) => {
    checkbox.addEventListener('change', (e) => {
      console.log('Checkbox changed:', { index, checked: e.target.checked });
      updateDeckSelection();
    });
  });

  // Initial updates
  updateDeckSelection();
  updatePreviewText();

  // Function to end study session
  function endStudySession() {
    fetch("/api/study/end-session/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": STUDY_CFG.csrfToken,
      },
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.success && data.session_summary) {
          // Show session summary
          const summary = data.session_summary;
          console.log("Study session ended:", summary);
        }
      })
      .catch((err) => console.error("Error ending session:", err));
  }

  // End session when user leaves the page
  window.addEventListener("beforeunload", endStudySession);

  // End session when user navigates away
  window.addEventListener("pagehide", endStudySession);

  // Load incorrect words count
  function loadIncorrectWordsCount() {
    // Check if required elements exist
    if (!reviewCountText || !reviewCount || !reviewModeOption) {
      console.log(
        "Review mode elements not found, skipping incorrect words count loading"
      );
      return;
    }

    fetch("/api/incorrect-words/count/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((r) => {
        console.log("API response status:", r.status);
        if (!r.ok) {
          throw new Error(`HTTP ${r.status}: ${r.statusText}`);
        }
        return r.json();
      })
      .then((data) => {
        console.log("API response data:", data);
        if (data.success) {
          const totalCount = data.counts.total;
          const counts = data.counts;
          console.log("Total incorrect words count:", totalCount);

          if (totalCount > 0) {
            // Update main count display
            reviewCountText.textContent = `${totalCount} ${
              STUDY_CFG.labels.incorrect_words_count ||
              "incorrect words to review"
            }`;
            reviewCount.style.display = "block";
            reviewModeOption.classList.remove("disabled");

            // Update detailed breakdown
            if (mcCount) mcCount.textContent = counts.mc || 0;
            if (typeCount) typeCount.textContent = counts.type || 0;
            if (dictationCount)
              dictationCount.textContent = counts.dictation || 0;

            // Show review details if any counts exist
            if (reviewDetails) reviewDetails.style.display = "block";

            // Enable start review button
            if (startBtnReview) {
              startBtnReview.disabled = false;
              startBtnReview.classList.remove("disabled");
            }

            console.log("Review mode enabled with", totalCount, "words");
          } else {
            reviewCount.style.display = "none";
            reviewModeOption.classList.add("disabled");
            if (reviewDetails) reviewDetails.style.display = "none";

            // Disable start review button
            if (startBtnReview) {
              startBtnReview.disabled = true;
              startBtnReview.classList.add("disabled");
            }

            console.log("Review mode disabled - no incorrect words found");
            // If review mode is selected but no words available, switch to decks mode
            if (currentStudyMode === "review") {
              const decksRadio = document.querySelector(
                'input[name="study_mode"][value="decks"]'
              );
              if (decksRadio) {
                decksRadio.checked = true;
                handleStudyModeChange();
              }
            }
          }
        } else {
          console.error("API returned success: false", data);
        }
      })
      .catch((err) => {
        console.error("Error loading incorrect words count:", err);
        // Disable review mode on error
        reviewCount.style.display = "none";
        reviewModeOption.classList.add("disabled");
      });
  }

  // Load favorites count
  function loadFavoritesCount() {
    console.log("🔍 Loading favorites count...");

    // Check if required elements exist
    const favoritesCountText = document.getElementById("favoritesCountText");
    const favoritesCount = document.getElementById("favoritesCount");
    const favoritesModeOption = document.getElementById("favoritesModeOption");

    console.log("🔍 Found elements:", {
      favoritesCountText: !!favoritesCountText,
      favoritesCount: !!favoritesCount,
      favoritesModeOption: !!favoritesModeOption
    });

    if (!favoritesCountText || !favoritesCount || !favoritesModeOption) {
      console.log(
        "❌ Favorites mode elements not found, skipping favorites count loading"
      );
      return;
    }

    fetch("/api/favorites/count/", {
      method: "GET",
      headers: {
        "X-CSRFToken": STUDY_CFG.csrfToken,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          const count = data.count;
          console.log(`Favorites count loaded: ${count}`);

          // Update the count display
          favoritesCountText.textContent = `${count} ${STUDY_CFG.labels.favorite_words_count || "favorite words"}`;

          // Show/hide count and enable/disable mode based on count
          if (count > 0) {
            favoritesCount.style.display = "block";
            favoritesModeOption.classList.remove("disabled");
            console.log("Favorites mode enabled");
          } else {
            favoritesCount.style.display = "none";
            favoritesModeOption.classList.add("disabled");
            console.log("Favorites mode disabled (no favorites)");
          }
        } else {
          console.error("Failed to load favorites count:", data.error);
          favoritesCount.style.display = "none";
          favoritesModeOption.classList.add("disabled");
        }
      })
      .catch((error) => {
        console.error("Error loading favorites count:", error);
        favoritesCount.style.display = "none";
        favoritesModeOption.classList.add("disabled");
      });
  }

  // Initialize incorrect words count
  loadIncorrectWordsCount();

  // Initialize favorites count
  loadFavoritesCount();

  // Initialize audio feedback system
  AudioFeedback.init();

  // Review Completion Modal Functions
  function showReviewCompletionModal() {
    const modal = document.getElementById("reviewCompletionModal");
    const continueBtn = document.getElementById("continueStudyingBtn");

    console.log("Showing review completion modal");

    if (modal) {
      modal.style.display = "flex";

      // Handle continue button click
      if (continueBtn) {
        continueBtn.onclick = function () {
          console.log("Continue studying button clicked");
          hideReviewCompletionModal();
          returnToStudySelection();
        };
      }

      // Close modal when clicking outside
      modal.onclick = function (e) {
        if (e.target === modal) {
          console.log("Modal overlay clicked - closing");
          hideReviewCompletionModal();
          returnToStudySelection();
        }
      };
    }
  }

  function hideReviewCompletionModal() {
    const modal = document.getElementById("reviewCompletionModal");
    if (modal) {
      modal.style.display = "none";
      console.log("Review completion modal hidden");
    }
  }

  function returnToStudySelection() {
    console.log("Returning to study selection after review completion");

    // Hide study area and show study selection
    if (studyArea) {
      studyArea.style.display = "none";
      studyArea.className = "study-area";
    }

    const studyModeSection = document.querySelector(".study-mode-section");
    if (studyModeSection) {
      studyModeSection.style.display = "block";
    }

    // Re-enable mode slider navigation when returning to study selection
    if (modeSliderInstance) {
      modeSliderInstance.enableEventListeners();
    }

    // Show appropriate options based on current mode
    if (currentStudyMode === "decks") {
      if (deckStudyOptions) deckStudyOptions.classList.remove("hidden");
      if (randomStudyOptions) randomStudyOptions.classList.add("hidden");
      if (reviewStudyOptions) reviewStudyOptions.classList.add("hidden");
    } else if (currentStudyMode === "review") {
      if (deckStudyOptions) deckStudyOptions.classList.add("hidden");
      if (randomStudyOptions) randomStudyOptions.classList.add("hidden");
      if (reviewStudyOptions) reviewStudyOptions.classList.remove("hidden");
    } else {
      if (deckStudyOptions) deckStudyOptions.classList.add("hidden");
      if (randomStudyOptions) randomStudyOptions.classList.remove("hidden");
      if (reviewStudyOptions) reviewStudyOptions.classList.add("hidden");
    }

    // Reset stats
    correctCnt = 0;
    incorrectCnt = 0;
    updateStats();
    if (studyHeader) studyHeader.style.display = "";

    // Refresh incorrect words count to update the interface
    console.log("Refreshing incorrect words count after completion");
    loadIncorrectWordsCount();
  }

  // Favorite button functionality for study mode
  function loadCardFavoriteStatus(cardId) {
    console.log(`[DEBUG] Loading favorite status for card ID: ${cardId}`);

    const favoriteBtn = document.getElementById("favoriteButton");
    if (!favoriteBtn) {
      console.warn(`[WARN] Favorite button not found when loading status for card ${cardId}`);
      return;
    }

    fetch(`/api/favorites/check/?card_ids[]=${cardId}`, {
      method: "GET",
      headers: {
        "X-CSRFToken": STUDY_CFG.csrfToken,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success && data.favorites[cardId] !== undefined) {
          const isFavorited = data.favorites[cardId];
          console.log(`[DEBUG] Card ${cardId} favorite status: ${isFavorited}`);
          updateStudyFavoriteButton(favoriteBtn, isFavorited);
        } else {
          console.warn(`[WARN] No favorite status data received for card ${cardId}`);
        }
      })
      .catch((error) => {
        console.error("Error loading favorite status:", error);
      });
  }

  function handleStudyFavoriteToggle(event) {
    event.preventDefault();
    event.stopPropagation();

    const button = event.currentTarget;
    const cardId = button.getAttribute("data-card-id");

    if (!cardId) {
      console.error("No card ID found for favorite button");
      return;
    }

    // Show loading state
    const originalIcon = button.querySelector(".favorite-icon").textContent;
    button.querySelector(".favorite-icon").textContent = "⏳";
    button.disabled = true;

    fetch("/api/favorites/toggle/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": STUDY_CFG.csrfToken,
      },
      body: JSON.stringify({
        card_id: cardId,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          updateStudyFavoriteButton(button, data.is_favorited);
          showStudyFavoriteMessage(data.is_favorited);
          console.log(
            `✅ Favorite toggled for card ${cardId}: ${
              data.is_favorited ? "added" : "removed"
            }`
          );

          // Refresh favorites count if we're in favorites mode
          if (currentStudyMode === "favorites") {
            loadFavoritesCount();
          }
        } else {
          console.error("Failed to toggle favorite:", data.error);
          // Restore original state
          button.querySelector(".favorite-icon").textContent = originalIcon;
        }
      })
      .catch((error) => {
        console.error("Error toggling favorite:", error);
        // Restore original state
        button.querySelector(".favorite-icon").textContent = originalIcon;
      })
      .finally(() => {
        button.disabled = false;
      });
  }

  function updateStudyFavoriteButton(button, isFavorited) {
    console.log(`[DEBUG] Updating favorite button visual state: ${isFavorited ? 'favorited' : 'not favorited'}`);

    const icon = button.querySelector(".favorite-icon");
    if (!icon) {
      console.error(`[ERROR] Favorite icon element not found in button`);
      return;
    }

    if (isFavorited) {
      icon.textContent = "❤️";
      button.classList.add("favorited");
      button.title = "Remove from favorites";
      console.log(`[DEBUG] Button updated to favorited state (❤️)`);
    } else {
      icon.textContent = "🤍";
      button.classList.remove("favorited");
      button.title = "Add to favorites";
      console.log(`[DEBUG] Button updated to unfavorited state (🤍)`);
    }
  }

  function showStudyFavoriteMessage(isFavorited) {
    const message = isFavorited ? "❤️ Added to favorites!" : "💔 Removed from favorites";

    // Create temporary message element
    const messageEl = document.createElement("div");
    messageEl.textContent = message;
    messageEl.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${isFavorited ? "#10b981" : "#ef4444"};
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      font-weight: 600;
      z-index: 1000;
      animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(messageEl);

    // Remove after 2 seconds
    setTimeout(() => {
      messageEl.style.animation = "slideOut 0.3s ease";
      setTimeout(() => {
        if (messageEl.parentNode) {
          messageEl.parentNode.removeChild(messageEl);
        }
      }, 300);
    }, 2000);
  }

  // Initialize timer display (hidden by default)
  if (timerDisplay) {
    timerDisplay.style.display = "none";
  }
  if (timerText) {
    timerText.textContent = "00:00";
  }

  // =============================================
  // AUTOMATIC TIMER PAUSE/RESUME FUNCTIONALITY
  // =============================================

  // Page Visibility API support check
  let hidden, visibilityChange;
  if (typeof document.hidden !== "undefined") {
    hidden = "hidden";
    visibilityChange = "visibilitychange";
  } else if (typeof document.msHidden !== "undefined") {
    hidden = "msHidden";
    visibilityChange = "msvisibilitychange";
  } else if (typeof document.webkitHidden !== "undefined") {
    hidden = "webkitHidden";
    visibilityChange = "webkitvisibilitychange";
  }

  // Handle page visibility changes (tab switching, minimizing browser)
  function handleVisibilityChange() {
    if (!studyStartTime) return; // Only handle if study session is active

    if (document[hidden]) {
      console.log(`[DEBUG] Page became hidden - pausing timer`);
      pauseStudyTimer();
    } else {
      console.log(`[DEBUG] Page became visible - resuming timer`);
      resumeStudyTimer();
    }
  }

  // Handle window focus/blur events (switching to other applications)
  function handleWindowBlur() {
    if (!studyStartTime) return; // Only handle if study session is active

    console.log(`[DEBUG] Window lost focus - pausing timer`);
    pauseStudyTimer();
  }

  function handleWindowFocus() {
    if (!studyStartTime) return; // Only handle if study session is active

    console.log(`[DEBUG] Window gained focus - resuming timer`);
    resumeStudyTimer();
  }

  // Add event listeners for automatic pause/resume
  if (typeof visibilityChange !== "undefined") {
    document.addEventListener(visibilityChange, handleVisibilityChange, false);
    console.log(`[DEBUG] Added Page Visibility API listener for ${visibilityChange}`);
  }

  // Add window focus/blur listeners as fallback and additional coverage
  window.addEventListener('blur', handleWindowBlur, false);
  window.addEventListener('focus', handleWindowFocus, false);
  console.log(`[DEBUG] Added window focus/blur listeners for timer pause/resume`);

  // Detailed Input Feedback System
  function showDetailedInputFeedback(correct, userAnswer, expectedAnswer) {
    console.log(`[DEBUG] Showing detailed feedback: correct=${correct}, user="${userAnswer}", expected="${expectedAnswer}"`);
    
    // Create feedback container
    const feedbackContainer = document.createElement('div');
    feedbackContainer.className = 'detailed-input-feedback';
    
    // Position it to the left of cardBox
    const cardBox = document.getElementById('cardBox');
    if (cardBox && cardBox.parentNode) {
      // Insert before cardBox (so it appears to the left)
      cardBox.parentNode.insertBefore(feedbackContainer, cardBox);
    } else {
      // Fallback: insert in study area
      const studyArea = document.getElementById('studyArea');
      if (studyArea) {
        studyArea.appendChild(feedbackContainer);
      }
    }
    
    if (correct) {
      // Correct answer feedback
      feedbackContainer.innerHTML = `
        <div class="feedback-content correct">
          <div class="feedback-header">
            <span class="feedback-icon">✅</span>
            <span class="feedback-title">Correct!</span>
            <button class="close-feedback-btn" onclick="this.parentElement.parentElement.parentElement.remove()">×</button>
          </div>
          <div class="answer-display">
            <span class="user-answer correct">"${userAnswer}"</span>
          </div>
        </div>
      `;
    } else {
      // Incorrect answer - show detailed comparison
      const comparisonHtml = generateLetterComparison(userAnswer, expectedAnswer);
      
      feedbackContainer.innerHTML = `
        <div class="feedback-content incorrect">
          <div class="feedback-header">
            <span class="feedback-icon">❌</span>
            <span class="feedback-title">Incorrect</span>
            <button class="close-feedback-btn" onclick="this.parentElement.parentElement.parentElement.remove()">×</button>
          </div>
          <div class="answer-comparison">
            <div class="answer-row">
              <span class="answer-label">Your answer:</span>
              <span class="user-answer incorrect">"${userAnswer}"</span>
            </div>
            <div class="answer-row">
              <span class="answer-label">Correct answer:</span>
              <span class="expected-answer">"${expectedAnswer}"</span>
            </div>
            <div class="letter-comparison">
              <span class="comparison-label">Letter by letter:</span>
              <div class="comparison-display">${comparisonHtml}</div>
            </div>
          </div>
        </div>
      `;
    }
    
    // Apply styles - position it as a sidebar
    feedbackContainer.style.cssText = `
      position: fixed;
      left: 20px;
      top: 50%;
      transform: translateY(-50%);
      width: 320px;
      max-height: 70vh;
      overflow-y: auto;
      background: ${correct ? 'linear-gradient(135deg, #10b981, #059669)' : 'linear-gradient(135deg, #ef4444, #dc2626)'};
      color: white;
      padding: 20px;
      border-radius: 16px;
      font-size: 14px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
      z-index: 1000;
      animation: slideInFromLeft 0.4s ease;
    `;
    
    // Auto-hide after some time with fade out
    setTimeout(() => {
      feedbackContainer.style.transition = 'opacity 1s ease';
      feedbackContainer.style.opacity = '0.6';
    }, 8000);
    
    // Auto-remove after longer time
    setTimeout(() => {
      if (feedbackContainer.parentNode) {
        feedbackContainer.style.transition = 'all 0.5s ease';
        feedbackContainer.style.opacity = '0';
        feedbackContainer.style.transform = 'translateX(-100%) translateY(-50%)';
        setTimeout(() => {
          if (feedbackContainer.parentNode) {
            feedbackContainer.remove();
          }
        }, 500);
      }
    }, 15000);
    
    // Inject CSS if not already present
    if (!document.getElementById('detailed-input-feedback-styles')) {
      const style = document.createElement('style');
      style.id = 'detailed-input-feedback-styles';
      style.textContent = `
        .detailed-input-feedback .feedback-content {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        
        .detailed-input-feedback .feedback-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          font-weight: 600;
          font-size: 16px;
        }
        
        .detailed-input-feedback .close-feedback-btn {
          background: rgba(255, 255, 255, 0.2);
          border: none;
          color: white;
          font-size: 20px;
          font-weight: bold;
          width: 28px;
          height: 28px;
          border-radius: 50%;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background-color 0.2s;
        }
        
        .detailed-input-feedback .close-feedback-btn:hover {
          background: rgba(255, 255, 255, 0.3);
        }
        
        .detailed-input-feedback .feedback-icon {
          font-size: 18px;
        }
        
        .detailed-input-feedback .answer-comparison {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .detailed-input-feedback .answer-row {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        
        .detailed-input-feedback .answer-label {
          font-size: 12px;
          opacity: 0.9;
          font-weight: 500;
        }
        
        .detailed-input-feedback .user-answer,
        .detailed-input-feedback .expected-answer {
          font-family: 'Courier New', monospace;
          font-size: 16px;
          font-weight: 600;
          padding: 6px 12px;
          border-radius: 6px;
          background-color: rgba(255, 255, 255, 0.2);
        }
        
        .detailed-input-feedback .letter-comparison {
          margin-top: 8px;
        }
        
        .detailed-input-feedback .comparison-label {
          font-size: 12px;
          opacity: 0.9;
          font-weight: 500;
          display: block;
          margin-bottom: 6px;
        }
        
        .detailed-input-feedback .comparison-display {
          font-family: 'Courier New', monospace;
          font-size: 16px;
          font-weight: 600;
          display: flex;
          flex-wrap: wrap;
          gap: 2px;
          padding: 8px;
          background-color: rgba(255, 255, 255, 0.1);
          border-radius: 6px;
        }
        
        .detailed-input-feedback .char-comparison {
          padding: 4px 6px;
          border-radius: 4px;
          font-weight: 600;
          min-width: 16px;
          text-align: center;
        }
        
        .detailed-input-feedback .char-correct {
          background-color: rgba(16, 185, 129, 0.3);
          color: #d1fae5;
        }
        
        .detailed-input-feedback .char-wrong {
          background-color: rgba(239, 68, 68, 0.4);
          color: #fecaca;
          font-size: 14px;
        }
        
        .detailed-input-feedback .char-missing {
          background-color: rgba(245, 158, 11, 0.4);
          color: #fef3c7;
          text-decoration: underline;
        }
        
        .detailed-input-feedback .char-extra {
          background-color: rgba(168, 85, 247, 0.4);
          color: #e9d5ff;
          text-decoration: line-through;
        }
        
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes slideInFromLeft {
          from {
            opacity: 0;
            transform: translateX(-100%) translateY(-50%);
          }
          to {
            opacity: 1;
            transform: translateX(0) translateY(-50%);
          }
        }
        
        /* Responsive design for mobile */
        @media (max-width: 768px) {
          .detailed-input-feedback {
            position: fixed !important;
            left: 10px !important;
            right: 10px !important;
            top: 20px !important;
            transform: none !important;
            width: auto !important;
            max-width: calc(100vw - 20px) !important;
          }
        }
        
        /* Ensure it doesn't interfere with small screens */
        @media (max-width: 1200px) {
          .detailed-input-feedback {
            width: 280px !important;
            left: 10px !important;
          }
        }
      `;
      document.head.appendChild(style);
    }
  }
  
  function generateLetterComparison(userAnswer, expectedAnswer) {
    const user = userAnswer.toLowerCase();
    const expected = expectedAnswer.toLowerCase();
    const maxLength = Math.max(user.length, expected.length);
    
    let comparisonHtml = '';
    
    for (let i = 0; i < maxLength; i++) {
      const userChar = user[i] || '';
      const expectedChar = expected[i] || '';
      
      let charClass = '';
      let displayChar = '';
      
      if (i >= user.length) {
        // Missing character
        charClass = 'char-missing';
        displayChar = expectedChar;
      } else if (i >= expected.length) {
        // Extra character
        charClass = 'char-extra';
        displayChar = userChar;
      } else if (userChar === expectedChar) {
        // Correct character
        charClass = 'char-correct';
        displayChar = userChar;
      } else {
        // Wrong character
        charClass = 'char-wrong';
        displayChar = `${userChar}→${expectedChar}`;
      }
      
      comparisonHtml += `<span class="char-comparison ${charClass}">${displayChar || ' '}</span>`;
    }
    
    return comparisonHtml;
  }

  // Voice Recording System
  const VoiceRecording = {
    mediaRecorder: null,
    audioChunks: [],
    recordedAudioBlob: null,
    recordedAudioUrl: null,
    isRecording: false,
    recordingTimeout: null, // Timeout for 4-second limit
    recognition: null,
    recognizedText: null,
    pronunciationScore: null,
    
    async init() {
      try {
        console.log("🎤 Initializing voice recording system...");
        
        if (!navigator.mediaDevices || !MediaRecorder) {
          console.warn("⚠️ MediaRecorder not supported");
          return false;
        }
        
        this.initSpeechRecognition();
        return true;
      } catch (error) {
        console.error("❌ Failed to initialize voice recording:", error);
        return false;
      }
    },
    
    initSpeechRecognition() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (!SpeechRecognition) {
        console.warn("⚠️ Speech Recognition not supported");
        this.showErrorFeedback('Speech recognition is not supported in this browser');
        return;
      }
      
      try {
      
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = 'en-US';
      this.recognition.maxAlternatives = 1;
      
      this.recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        
        // Show live transcription
        const currentTranscript = finalTranscript || interimTranscript;
        this.showLiveTranscription(currentTranscript.toLowerCase().trim());
        
        // If we have final transcript, assess pronunciation
        if (finalTranscript) {
          const transcript = finalTranscript.toLowerCase().trim();
          const confidence = event.results[event.results.length - 1][0].confidence || 0.5;
          
          console.log("🎤 Final Recognition:", transcript, "Confidence:", confidence);
          
          this.recognizedText = transcript;
          this.assessPronunciation(transcript, confidence);
        }
      };
      
      this.recognition.onerror = (event) => {
        console.error("❌ Speech Recognition Error:", event.error);
        
        // Handle different error types and provide feedback
        if (event.error === 'no-speech') {
          console.log("ℹ️ No speech detected");
          this.showNoSpeechFeedback();
        } else if (event.error === 'not-allowed') {
          alert('Microphone permission is required for pronunciation checking');
        } else if (event.error === 'network') {
          this.showErrorFeedback('Network error - please check your internet connection');
        } else {
          this.showErrorFeedback(`Speech recognition error: ${event.error}`);
        }
      };
      
      this.recognition.onend = () => {
        console.log("🎤 Speech Recognition ended");
        
        // If we haven't gotten any transcript yet, provide feedback
        if (!this.recognizedText && this.isRecording) {
          setTimeout(() => {
            if (!this.recognizedText) {
              this.showNoSpeechFeedback();
            }
          }, 500); // Wait 500ms for any delayed results
        }
      };
      
      } catch (error) {
        console.error("❌ Failed to initialize Speech Recognition:", error);
        this.showErrorFeedback('Failed to initialize speech recognition');
      }
    },
    
    async startRecording() {
      try {
        if (this.isRecording) return;
        
        this.clearPronunciationFeedback();
        
        // Clear live transcription from previous recording
        const transcriptionEl = document.querySelector('.live-transcription');
        if (transcriptionEl) {
          transcriptionEl.remove();
        }
        
        this.recognizedText = null;
        this.pronunciationScore = null;
        this.audioChunks = [];
        
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        this.mediaRecorder = new MediaRecorder(stream);
        
        this.mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            this.audioChunks.push(event.data);
          }
        };
        
        this.mediaRecorder.onstop = () => {
          this.recordedAudioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
          if (this.recordedAudioUrl) {
            URL.revokeObjectURL(this.recordedAudioUrl);
          }
          this.recordedAudioUrl = URL.createObjectURL(this.recordedAudioBlob);
          
          const playBtn = document.getElementById('playRecordingButton');
          if (playBtn) {
            playBtn.style.display = 'block';
          }
          
          stream.getTracks().forEach(track => track.stop());
        };
        
        this.isRecording = true;
        this.mediaRecorder.start();
        
        // Start speech recognition separately
        if (this.recognition) {
          this.recognition.start();
        }
        
        // Set 4-second timeout to auto-stop recording
        this.recordingTimeout = setTimeout(() => {
          if (this.isRecording) {
            console.log("⏰ Recording auto-stopped after 4 seconds");
            this.stopRecording();
          }
        }, 4000);
        
        // Update UI
        const recordBtn = document.getElementById('recordButton');
        const recordIcon = document.getElementById('recordIcon');
        if (recordBtn && recordIcon) {
          recordBtn.classList.add('recording');
          recordIcon.className = 'fas fa-stop';
          recordBtn.title = STUDY_CFG.labels.stop_recording || 'Stop recording';
        }
        
        console.log("🔴 Recording started");
        
      } catch (error) {
        console.error("❌ Failed to start recording:", error);
        alert(STUDY_CFG.labels.microphone_error || 'Microphone access denied');
        this.isRecording = false;
      }
    },
    
    stopRecording() {
      if (!this.isRecording) return;
      
      this.isRecording = false;
      
      // Clear the recording timeout if it exists
      if (this.recordingTimeout) {
        clearTimeout(this.recordingTimeout);
        this.recordingTimeout = null;
      }
      
      if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
        this.mediaRecorder.stop();
      }
      
      if (this.recognition) {
        try {
          this.recognition.stop();
        } catch (error) {
          console.warn("⚠️ Could not stop speech recognition:", error);
        }
      }
      
      // Update UI
      const recordBtn = document.getElementById('recordButton');
      const recordIcon = document.getElementById('recordIcon');
      if (recordBtn && recordIcon) {
        recordBtn.classList.remove('recording');
        recordIcon.className = 'fas fa-microphone';
        recordBtn.title = STUDY_CFG.labels.record_pronunciation || 'Record pronunciation';
      }
      
      // Set a timeout to check if we got any transcript
      setTimeout(() => {
        if (!this.recognizedText) {
          this.showNoSpeechFeedback();
        }
      }, 1000); // Give 1 second for speech recognition to process
      
      console.log("⏹️ Recording stopped");
    },
    
    playRecording() {
      if (!this.recordedAudioUrl) {
        console.warn("⚠️ No recorded audio available");
        return;
      }
      
      const audio = new Audio(this.recordedAudioUrl);
      audio.play().then(() => {
        console.log("🎤 Playing recorded audio");
      }).catch(error => {
        console.error("❌ Error playing audio:", error);
      });
    },
    
    showLiveTranscription(transcript) {
      if (!transcript || !currentQuestion || !currentQuestion.word) return;
      
      const expected = currentQuestion.word.toLowerCase().trim();
      const spoken = transcript.toLowerCase().trim();
      
      // Check if current transcript matches expected word
      const isCorrect = expected === spoken || spoken.includes(expected);
      
      // Create or update transcription display
      let transcriptionEl = document.querySelector('.live-transcription');
      if (!transcriptionEl) {
        transcriptionEl = document.createElement('div');
        transcriptionEl.className = 'live-transcription';
        
        const recordingControls = document.querySelector('.recording-controls');
        if (recordingControls && recordingControls.parentNode) {
          recordingControls.parentNode.insertBefore(transcriptionEl, recordingControls.nextSibling);
        }
      }
      
      // Style based on correctness
      const bgColor = isCorrect ? '#10b981' : '#ef4444';
      const textColor = 'white';
      const icon = isCorrect ? '✅' : '❌';
      
      transcriptionEl.innerHTML = `
        <div class="transcription-content">
          <span class="transcription-icon">${icon}</span>
          <span class="transcription-text">"${spoken}"</span>
        </div>
      `;
      
      transcriptionEl.style.cssText = `
        background: ${bgColor};
        color: ${textColor};
        padding: 8px 12px;
        border-radius: 8px;
        margin-top: 8px;
        font-size: 0.9rem;
        font-weight: 500;
        animation: fadeIn 0.2s ease;
        display: block;
      `;
      
      console.log(`🎯 Live transcription: "${spoken}" (${isCorrect ? 'CORRECT' : 'INCORRECT'})`);
    },
    
    assessPronunciation(recognizedText, confidence) {
      if (!currentQuestion || !currentQuestion.word) {
        console.warn("⚠️ No current question");
        return;
      }
      
      const expected = currentQuestion.word.toLowerCase().trim();
      const spoken = recognizedText.toLowerCase().trim();
      
      const score = this.calculateSimilarityScore(expected, spoken, confidence);
      this.pronunciationScore = score;
      
      this.showPronunciationFeedback(expected, spoken, score, confidence);
      
      console.log(`🎯 Pronunciation: ${expected} vs ${spoken}, Score: ${score}%`);
    },
    
    calculateSimilarityScore(expected, spoken, confidence) {
      if (expected === spoken) {
        return Math.min(95 + (confidence * 5), 100);
      }
      
      if (spoken.includes(expected) || expected.includes(spoken)) {
        return Math.min(80 + (confidence * 15), 95);
      }
      
      const distance = this.levenshteinDistance(expected, spoken);
      const maxLength = Math.max(expected.length, spoken.length);
      const similarity = (maxLength - distance) / maxLength;
      
      const baseScore = similarity * 70;
      const confidenceBonus = confidence * 30;
      
      return Math.max(0, Math.min(100, baseScore + confidenceBonus));
    },
    
    levenshteinDistance(str1, str2) {
      const matrix = [];
      
      for (let i = 0; i <= str2.length; i++) {
        matrix[i] = [i];
      }
      
      for (let j = 0; j <= str1.length; j++) {
        matrix[0][j] = j;
      }
      
      for (let i = 1; i <= str2.length; i++) {
        for (let j = 1; j <= str1.length; j++) {
          if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
            matrix[i][j] = matrix[i - 1][j - 1];
          } else {
            matrix[i][j] = Math.min(
              matrix[i - 1][j - 1] + 1,
              matrix[i][j - 1] + 1,
              matrix[i - 1][j] + 1
            );
          }
        }
      }
      
      return matrix[str2.length][str1.length];
    },
    
    showPronunciationFeedback(expected, spoken, score, confidence) {
      this.clearPronunciationFeedback();
      
      const feedbackEl = document.createElement('div');
      feedbackEl.className = 'pronunciation-feedback';
      
      const recordingControls = document.querySelector('.recording-controls');
      if (recordingControls && recordingControls.parentNode) {
        recordingControls.parentNode.insertBefore(feedbackEl, recordingControls.nextSibling);
      }
      
      // Check if pronunciation is correct (exact match or very close)
      const isCorrect = expected === spoken || score >= 80;
      
      let feedbackClass, wordColor, feedbackMessage;
      
      if (isCorrect) {
        feedbackClass = 'feedback-correct';
        wordColor = '#10b981'; // Green
        feedbackMessage = `✅ Correct: "${spoken}"`;
      } else {
        feedbackClass = 'feedback-incorrect';
        wordColor = '#ef4444'; // Red  
        feedbackMessage = `❌ You said: "${spoken}" (Expected: "${expected}")`;
      }
      
      feedbackEl.className = `pronunciation-feedback ${feedbackClass}`;
      feedbackEl.innerHTML = `
        <div class="feedback-content">
          <div class="feedback-text">
            <div class="feedback-message">${feedbackMessage}</div>
            <div class="feedback-score">Score: ${Math.round(score)}%</div>
          </div>
        </div>
      `;
      
      // Style the recognized word with appropriate color
      feedbackEl.style.cssText = `
        background: ${isCorrect ? 'linear-gradient(135deg, #10b981, #059669)' : 'linear-gradient(135deg, #ef4444, #dc2626)'};
        color: white;
        margin-top: 12px;
        padding: 12px 16px;
        border-radius: 12px;
        animation: slideIn 0.3s ease;
      `;
      
      setTimeout(() => {
        feedbackEl.style.opacity = '0.7';
      }, 4000);
    },
    
    clearPronunciationFeedback() {
      const feedbackEl = document.querySelector('.pronunciation-feedback');
      if (feedbackEl) {
        feedbackEl.remove();
      }
    },
    
    showNoSpeechFeedback() {
      this.clearPronunciationFeedback();
      
      const feedbackEl = document.createElement('div');
      feedbackEl.className = 'pronunciation-feedback feedback-warning';
      
      const recordingControls = document.querySelector('.recording-controls');
      if (recordingControls && recordingControls.parentNode) {
        recordingControls.parentNode.insertBefore(feedbackEl, recordingControls.nextSibling);
      }
      
      feedbackEl.innerHTML = `
        <div class="feedback-content">
          <div class="feedback-text">
            <div class="feedback-message">🤐 No speech detected</div>
            <div class="feedback-score">Try speaking louder or closer to microphone</div>
          </div>
        </div>
      `;
      
      feedbackEl.style.cssText = `
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        margin-top: 12px;
        padding: 12px 16px;
        border-radius: 12px;
        animation: slideIn 0.3s ease;
      `;
      
      setTimeout(() => {
        feedbackEl.style.opacity = '0.7';
      }, 4000);
    },
    
    showErrorFeedback(message) {
      this.clearPronunciationFeedback();
      
      const feedbackEl = document.createElement('div');
      feedbackEl.className = 'pronunciation-feedback feedback-error';
      
      const recordingControls = document.querySelector('.recording-controls');
      if (recordingControls && recordingControls.parentNode) {
        recordingControls.parentNode.insertBefore(feedbackEl, recordingControls.nextSibling);
      }
      
      feedbackEl.innerHTML = `
        <div class="feedback-content">
          <div class="feedback-text">
            <div class="feedback-message">❌ ${message}</div>
          </div>
        </div>
      `;
      
      feedbackEl.style.cssText = `
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        margin-top: 12px;
        padding: 12px 16px;
        border-radius: 12px;
        animation: slideIn 0.3s ease;
      `;
      
      setTimeout(() => {
        feedbackEl.style.opacity = '0.7';
      }, 5000);
    },
    
    clearRecording() {
      const playBtn = document.getElementById('playRecordingButton');
      if (playBtn) {
        playBtn.style.display = 'none';
      }
      
      if (this.recordedAudioUrl) {
        URL.revokeObjectURL(this.recordedAudioUrl);
        this.recordedAudioUrl = null;
      }
      this.recordedAudioBlob = null;
      this.audioChunks = [];
      this.clearPronunciationFeedback();
      
      // Clear live transcription
      const transcriptionEl = document.querySelector('.live-transcription');
      if (transcriptionEl) {
        transcriptionEl.remove();
      }
      
      this.recognizedText = null;
      this.pronunciationScore = null;
    }
  };

  // Initialize Voice Recording
  VoiceRecording.init().then(supported => {
    const recordButton = document.getElementById('recordButton');
    const playRecordingButton = document.getElementById('playRecordingButton');
    
    if (supported && recordButton) {
      recordButton.addEventListener('click', () => {
        if (VoiceRecording.isRecording) {
          VoiceRecording.stopRecording();
        } else {
          VoiceRecording.startRecording();
        }
      });
    }
    
    if (playRecordingButton) {
      playRecordingButton.addEventListener('click', () => {
        VoiceRecording.playRecording();
      });
    }
  });

  // Make functions globally available
  window.showReviewCompletionModal = showReviewCompletionModal;
  window.hideReviewCompletionModal = hideReviewCompletionModal;
  window.returnToStudySelection = returnToStudySelection;
  window.loadCardFavoriteStatus = loadCardFavoriteStatus;
  window.handleStudyFavoriteToggle = handleStudyFavoriteToggle;
})();
