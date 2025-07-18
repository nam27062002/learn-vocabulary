// static/js/deck_detail.js

document.addEventListener('DOMContentLoaded', function() {
    const carouselContainer = document.querySelector('#carousel-container');
    if (!carouselContainer) {
        return;
    }

    const carouselSlides = carouselContainer.querySelector('#carousel-slides');
    const slides = Array.from(carouselSlides.children);
    const prevBtn = carouselContainer.querySelector('#prevBtn');
    const nextBtn = carouselContainer.querySelector('#nextBtn');
    const paginationDotsContainer = document.querySelector('#pagination-dots');

    let currentSlideIndex = 0;

    function showSlide(index) {
        // Ensure the index loops around
        if (index < 0) {
            currentSlideIndex = slides.length - 1;
        } else if (index >= slides.length) {
            currentSlideIndex = 0;
        }

        const currentSlide = slides[currentSlideIndex];
        
        // The scrollLeft will be the offset of the current slide
        const targetScrollLeft = currentSlide.offsetLeft; 

        carouselSlides.scrollTo({
            left: targetScrollLeft,
            behavior: 'smooth'
        });

        // Apply shadow/peek effect dynamically via inline styles
        slides.forEach((slide, i) => {
            if (i === currentSlideIndex) {
                slide.style.opacity = '1';
                slide.style.transform = 'scale(1)';
                slide.style.zIndex = '2';
            } else {
                slide.style.opacity = '0.7';
                slide.style.transform = 'scale(0.9)';
                slide.style.zIndex = '1';
            }
        });

        updatePagination();
    }

    function nextSlide() {
        currentSlideIndex++;
        showSlide(currentSlideIndex);
    }

    function prevSlide() {
        currentSlideIndex--;
        showSlide(currentSlideIndex);
    }

    function updatePagination() {
        if (paginationDotsContainer) {
            paginationDotsContainer.innerHTML = '';
            slides.forEach((_, index) => {
                const dot = document.createElement('span');
                dot.classList.add('pagination-dot');
                if (index === currentSlideIndex) {
                    dot.classList.add('active');
                }
                dot.addEventListener('click', () => showSlide(index));
                paginationDotsContainer.appendChild(dot);
            });
        }
    }

    // Event listeners for navigation buttons
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            prevSlide();
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            nextSlide();
        });
    }

    // Event listener for audio icons
    carouselSlides.addEventListener('click', function(event) {
        const audioIcon = event.target.closest('.audio-icon');
        if (audioIcon) {
            const audioUrl = audioIcon.dataset.audioUrl;
            if (audioUrl) {
                try {
                    new Audio(audioUrl).play().catch(e => console.error('Audio playback error:', e));
                } catch (e) {
                    console.error('Error creating Audio object:', e);
                }
            }
        }
    });

    // Initial setup
    showSlide(currentSlideIndex);

    // Keyboard navigation
    document.addEventListener('keydown', function(event) {
        if (event.key === 'ArrowLeft') {
            prevSlide();
        } else if (event.key === 'ArrowRight') {
            nextSlide();
        }
    });

    // Swipe/Drag functionality
    let startX;
    let isDragging = false;
    let initialScrollLeft;

    carouselSlides.addEventListener('mousedown', (e) => {
        isDragging = true;
        startX = e.pageX;
        initialScrollLeft = carouselSlides.scrollLeft;
        carouselSlides.style.cursor = 'grabbing';
    });

    carouselSlides.addEventListener('mouseleave', () => {
        if (isDragging) {
            isDragging = false;
            carouselSlides.style.cursor = 'grab';
        }
    });

    carouselSlides.addEventListener('mouseup', () => {
        isDragging = false;
        carouselSlides.style.cursor = 'grab';
        // When mouseup, let scroll-snap handle the snapping.
        // No need to call showSlide here explicitly for snapping.
    });

    carouselSlides.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        e.preventDefault();
        const x = e.pageX;
        const walk = (x - startX) * 1.5;
        carouselSlides.scrollLeft = initialScrollLeft - walk;
    });

    carouselSlides.addEventListener('touchend', (e) => {
        const endX = e.changedTouches[0].pageX;
        const threshold = 50;
        if (startX - endX > threshold) {
            // Let scroll-snap handle the transition for next/prev
            nextSlide();
        } else if (endX - startX > threshold) {
            // Let scroll-snap handle the transition for next/prev
            prevSlide();
        }
    });

    carouselSlides.addEventListener('touchstart', (e) => {
        startX = e.touches[0].pageX;
        initialScrollLeft = carouselSlides.scrollLeft;
    });

    carouselSlides.addEventListener('touchmove', (e) => {
        const x = e.touches[0].pageX;
        const walk = (x - startX) * 1.5;
        carouselSlides.scrollLeft = initialScrollLeft - walk;
    });
}); 