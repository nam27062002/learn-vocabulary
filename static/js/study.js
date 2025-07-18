// study.js - handles study session with multiple modes

(function(){
  const deckSelect = document.getElementById('deckSelect');
  const startBtn = document.getElementById('startBtn');
  const deckSelectWrapper = document.getElementById('deckSelectWrapper');
  const studyArea = document.getElementById('studyArea');
  const cardWordEl = document.getElementById('cardWord');
  const cardPhoneticEl = document.getElementById('cardPhonetic');
  const cardImageEl = document.getElementById('cardImage');
  const cardDefsEl = document.getElementById('cardDefs');
  const answerArea = document.getElementById('answerSection') || {innerHTML:'', appendChild:()=>{}, style:{}};
  const feedbackMsg = document.getElementById('feedbackMsg') || {style:{},textContent:''};
  const noCardMsg = document.getElementById('noCardMsg') || {style:{}};
  const optionsArea = document.getElementById('optionsArea') || answerArea;
  const backBtn = document.getElementById('backBtn');
  const statsInfo = document.getElementById('statsInfo');
  let correctCnt=0, incorrectCnt=0;
  let nextTimeout=null;

  function updateStats(){
    if(statsInfo){
      statsInfo.textContent=`${STUDY_CFG.labels.correct}: ${correctCnt} | ${STUDY_CFG.labels.incorrect}: ${incorrectCnt}`;
    }
  }

  const modeSelect = null; // removed
  let currentQuestion = null;

  function qsToParams(){
    const params = new URLSearchParams();
    Array.from(deckSelect.selectedOptions).forEach(o=>params.append('deck_ids[]', o.value));
    return params.toString();
  }

  function fetchNext(){
    fetch(`${STUDY_CFG.nextUrl}?${qsToParams()}`)
      .then(r=>r.json())
      .then(data=>{
        if(data.done){
          noCardMsg.style.display='block';
          studyArea.style.display='none';
          return;
        }
        renderQuestion(data.question);
      });
  }

  function renderQuestion(q){
    currentQuestion = q;
    feedbackMsg.style.display='none';
    if(cardWordEl){cardWordEl.textContent='';}
    if(cardPhoneticEl){cardPhoneticEl.style.display='none';}
    if(cardImageEl){
      if(q.image_url){
        cardImageEl.src=q.image_url;
        cardImageEl.style.display='block';
      }else{
        cardImageEl.style.display='none';
      }
    }
    if(cardDefsEl){cardDefsEl.textContent=q.definitions.map(d=>`EN: ${d.english_definition}\nVI: ${d.vietnamese_definition}`).join('\n\n');}

    optionsArea.innerHTML='';
    if(q.type==='mc'){
      q.options.forEach(opt=>{
        const btn=document.createElement('button');
        btn.textContent=opt;
        btn.className='option-btn';
        btn.addEventListener('click',()=>submitAnswer(opt===q.word));
        optionsArea.appendChild(btn);
      });
    }else{
      const inp=document.createElement('input');
      inp.type='text';
      inp.placeholder=STUDY_CFG.labels.placeholder;
      inp.className='type-input';
      const btn=document.createElement('button');
      btn.textContent=STUDY_CFG.labels.check;
      btn.className='check-btn';
      btn.addEventListener('click',()=>{
        const correct=inp.value.trim().toLowerCase()===q.answer.toLowerCase();
        submitAnswer(correct);
      });
      inp.addEventListener('keydown', (e)=>{
        if(e.key==='Enter'){
          e.preventDefault();
          btn.click();
        }
      });
      optionsArea.appendChild(inp);
      optionsArea.appendChild(btn);
      if(answerArea.style){answerArea.style.display='block';}
      return;
    }
    if(answerArea.style){answerArea.style.display='block';}
  }

  function submitAnswer(correct){
    feedbackMsg.style.display='block';
    if(correct){
      correctCnt++;
      feedbackMsg.textContent=STUDY_CFG.labels.correct;
      feedbackMsg.style.color='#38c172';
    }else{
      incorrectCnt++;
      const label=STUDY_CFG.labels.answerLabel||'Đáp án';
      feedbackMsg.textContent=`${STUDY_CFG.labels.incorrect} – ${label}: ${currentQuestion.word}`;
      feedbackMsg.style.color='#e3342f';
    }
    updateStats();

    fetch(STUDY_CFG.submitUrl,{
      method:'POST',
      headers:{'Content-Type':'application/json','X-CSRFToken':STUDY_CFG.csrfToken},
      body:JSON.stringify({card_id:currentQuestion.id, correct:correct})
    }).then(()=>{
      if(correct && currentQuestion.audio_url){
        try{
          const audio=new Audio(currentQuestion.audio_url);
          audio.play().catch(()=>{});
          audio.addEventListener('ended',()=>{
            fetchNext();
          });
          // Fallback in case 'ended' not fired
          nextTimeout=setTimeout(fetchNext,8000);
        }catch(e){
          nextTimeout=setTimeout(fetchNext,1000);
        }
      }else{
        nextTimeout=setTimeout(fetchNext,1000);
      }
    });
  }

  startBtn.addEventListener('click',()=>{
    if(deckSelect.selectedOptions.length===0){alert('Please select at least one deck');return;}
    deckSelectWrapper.style.display='none';
    correctCnt=0; incorrectCnt=0; updateStats();
    studyArea.style.display='block';
    if(cardPhoneticEl){cardPhoneticEl.style.display='none';}
    fetchNext();
  });

  backBtn.addEventListener('click',()=>{
    deckSelectWrapper.style.display='block';
    studyArea.style.display='none';
  });
})(); 