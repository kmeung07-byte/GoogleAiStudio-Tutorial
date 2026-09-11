    let player = null;
    let isPlayerReady = false;
    let currentVideoId = null;
    let videoData = null;
    let timeUpdateInterval = null;

    // ================= 배경 선택 토글 스위치 로직 (검은색 / 하얀색) =================
    let currentTheme = localStorage.getItem('yt_ai_theme') || 'dark';
    if (currentTheme !== 'light' && currentTheme !== 'dark') currentTheme = 'dark';

    function applyTheme(themeKey) {
      currentTheme = (themeKey === 'light') ? 'light' : 'dark';
      document.body.className = `theme-${currentTheme} min-h-screen font-sans antialiased flex flex-col transition-colors duration-300`;

      const btnToggle = document.getElementById('btn-theme-toggle');
      const knob = document.getElementById('theme-toggle-knob');

      if (btnToggle && knob) {
        if (currentTheme === 'light') {
          // 하얀색 (Light Mode): 토글 핸들이 오른쪽으로 부드럽게 이동
          btnToggle.setAttribute('aria-checked', 'true');
          btnToggle.title = '현재 배경: 하얀색 (클릭 시 검은색으로 변경)';
          btnToggle.classList.remove('bg-[#1a2332]');
          btnToggle.classList.add('bg-[#e2e8f0]');

          knob.classList.remove('translate-x-0.5', 'bg-[#8e9aa8]');
          knob.classList.add('translate-x-6', 'bg-[#475569]');
        } else {
          // 검은색 (Dark Mode): 토글 핸들이 왼쪽 위치 (이미지 레퍼런스 스타일)
          btnToggle.setAttribute('aria-checked', 'false');
          btnToggle.title = '현재 배경: 검은색 (클릭 시 하얀색으로 변경)';
          btnToggle.classList.remove('bg-[#e2e8f0]');
          btnToggle.classList.add('bg-[#1a2332]');

          knob.classList.remove('translate-x-6', 'bg-[#475569]');
          knob.classList.add('translate-x-0.5', 'bg-[#8e9aa8]');
        }
      }

      localStorage.setItem('yt_ai_theme', currentTheme);
    }

    // 토글 버튼 클릭 이벤트
    const btnThemeToggle = document.getElementById('btn-theme-toggle');
    if (btnThemeToggle) {
      btnThemeToggle.addEventListener('click', () => {
        applyTheme(currentTheme === 'dark' ? 'light' : 'dark');
      });
    }

    // 페이지 로드 시 즉시 테마 적용
    applyTheme(currentTheme);

    // 1. YouTube IFrame API Ready Callback
    function onYouTubeIframeAPIReady() {
      // player will be initialized when a URL is submitted
    }

    function initYouTubePlayer(videoId) {
      currentVideoId = videoId;
      document.getElementById('player-placeholder').classList.add('hidden');
      document.getElementById('yt-player-container').classList.remove('hidden');

      if (player) {
        player.loadVideoById(videoId);
        return;
      }

      player = new YT.Player('yt-player', {
        videoId: videoId,
        playerVars: {
          autoplay: 1,
          controls: 1,
          modestbranding: 1,
          rel: 0,
        },
        events: {
          'onReady': onPlayerReady,
          'onStateChange': onPlayerStateChange
        }
      });
    }

    function onPlayerReady(event) {
      isPlayerReady = true;
      const initialVol = parseInt(document.getElementById('volume-slider').value) || 80;
      player.setVolume(initialVol);
      updateVolumeUI(initialVol);

      // Start time tracking loop
      if (timeUpdateInterval) clearInterval(timeUpdateInterval);
      timeUpdateInterval = setInterval(updateTimeDisplay, 500);
    }

    function onPlayerStateChange(event) {
      const playIcon = document.getElementById('play-icon');
      if (event.data === YT.PlayerState.PLAYING) {
        playIcon.className = 'fa-solid fa-pause text-xs';
      } else {
        playIcon.className = 'fa-solid fa-play text-xs ml-0.5';
      }
    }

    function updateTimeDisplay() {
      if (!player || !isPlayerReady || typeof player.getCurrentTime !== 'function') return;
      const cur = Math.floor(player.getCurrentTime()) || 0;
      const dur = Math.floor(player.getDuration()) || 0;
      document.getElementById('video-time-display').innerText = `${formatSeconds(cur)} / ${formatSeconds(dur)}`;
    }

    function formatSeconds(sec) {
      const m = Math.floor(sec / 60);
      const s = Math.floor(sec % 60);
      return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }

    // Play/Pause button
    document.getElementById('btn-toggle-play').addEventListener('click', () => {
      if (!player || !isPlayerReady) return;
      const state = player.getPlayerState();
      if (state === YT.PlayerState.PLAYING) {
        player.pauseVideo();
      } else {
        player.playVideo();
      }
    });

    // Volume Slider & Mute
    const volSlider = document.getElementById('volume-slider');
    const volPercent = document.getElementById('volume-percent');
    const btnMute = document.getElementById('btn-mute-toggle');
    const volIcon = document.getElementById('volume-icon');

    volSlider.addEventListener('input', (e) => {
      const val = parseInt(e.target.value);
      if (player && isPlayerReady) {
        player.unMute();
        player.setVolume(val);
      }
      updateVolumeUI(val);
    });

    btnMute.addEventListener('click', () => {
      if (!player || !isPlayerReady) return;
      if (player.isMuted()) {
        player.unMute();
        const currentVol = player.getVolume();
        volSlider.value = currentVol;
        updateVolumeUI(currentVol);
      } else {
        player.mute();
        updateVolumeUI(0, true);
      }
    });

    function updateVolumeUI(val, isMuted = false) {
      volPercent.innerText = `${val}%`;
      if (isMuted || val === 0) {
        volIcon.className = 'fa-solid fa-volume-xmark text-xs text-red-400';
      } else if (val < 50) {
        volIcon.className = 'fa-solid fa-volume-low text-xs text-neutral-300';
      } else {
        volIcon.className = 'fa-solid fa-volume-high text-xs text-neutral-300';
      }
    }

    // Paste button in Header
    document.getElementById('btn-paste-url').addEventListener('click', async () => {
      try {
        const text = await navigator.clipboard.readText();
        if (text) document.getElementById('input-youtube-url').value = text.trim();
      } catch (err) {
        console.warn('Clipboard read failed:', err);
      }
    });

    // Sample Chips
    document.querySelectorAll('.sample-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        document.getElementById('input-youtube-url').value = btn.getAttribute('data-url');
        document.getElementById('url-form').dispatchEvent(new Event('submit'));
      });
    });

    // Submit URL -> Load Video & Background STT
    document.getElementById('url-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const url = document.getElementById('input-youtube-url').value.trim();
      if (!url) return;

      // URL 파싱으로 비디오 ID 추출
      const match = url.match(/(?:watch\?v=|embed\/|v\/|shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
      if (!match) {
        alert('올바른 유튜브 링크를 입력해주세요.');
        return;
      }
      const videoId = match[1];

      // 1. 영상 즉시 로드
      initYouTubePlayer(videoId);

      // 2. 상태 업데이트
      const badge = document.getElementById('stt-status-badge');
      const text = document.getElementById('stt-status-text');
      badge.className = 'flex items-center space-x-1.5 text-amber-400 animate-pulse';
      badge.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-xs"></i><span id="stt-status-text">오디오 추출 & Gemini 3.5 Transcribe 전사 중...</span>';

      try {
        const res = await fetch('/api/video-init', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: url })
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
          throw new Error(data.detail || '영상 처리 실패');
        }

        videoData = data;
        document.getElementById('video-title-display').innerText = data.video.title || '';

        // 전사 완료 상태
        if (data.source === 'csv' || data.source === 'memory') {
          badge.className = 'flex items-center space-x-1.5 text-cyan-400 font-medium';
          badge.innerHTML = '<i class="fa-solid fa-database text-xs"></i><span>저장된 CSV에서 즉시 로드됨 (재전사 불필요)</span>';
        } else {
          badge.className = 'flex items-center space-x-1.5 text-emerald-400 font-medium';
          badge.innerHTML = '<i class="fa-solid fa-check-circle text-xs"></i><span>Gemini 3.5 전사 완료 & CSV 저장됨</span>';
        }

        // 렌더링
        renderTimeline(data.transcription.segments);

      } catch (err) {
        badge.className = 'flex items-center space-x-1.5 text-rose-400';
        badge.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-xs"></i><span>전사 오류: ${err.message}</span>`;
      }
    });

    // ================= 영상 내 특정 내용 검색 & 해당 시간 이동 PLAY =================
    document.getElementById('content-search-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const query = document.getElementById('input-content-query').value.trim();
      if (!query) return;

      if (!videoData || !currentVideoId) {
        alert('먼저 상단에서 유튜브 영상을 검색하여 로드해주세요.');
        return;
      }

      const btnSearch = document.getElementById('btn-content-search');
      btnSearch.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-xs"></i>';
      btnSearch.disabled = true;

      try {
        const res = await fetch('/api/search-content', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            video_id: currentVideoId,
            query: query
          })
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
          throw new Error(data.detail || '내용 검색 실패');
        }

        const match = data.match;
        if (match.matched && match.target_seconds !== undefined) {
          jumpAndPlay(match.target_seconds, match.display_time, match.explanation || match.quote);
        } else {
          showJumpBanner('00:00', match.explanation || '영상 내에서 일치하는 내용을 찾지 못했습니다.');
        }

      } catch (err) {
        alert('검색 오류: ' + err.message);
      } finally {
        btnSearch.innerHTML = '<i class="fa-solid fa-magnifying-glass text-sm"></i>';
        btnSearch.disabled = false;
      }
    });

    function jumpAndPlay(seconds, displayTime, text) {
      if (player && isPlayerReady) {
        player.seekTo(seconds, true);
        player.playVideo();
      }
      showJumpBanner(displayTime, text);
    }

    function showJumpBanner(displayTime, text) {
      const banner = document.getElementById('jump-banner');
      document.getElementById('jump-timestamp').innerText = displayTime;
      document.getElementById('jump-text').innerText = text;
      banner.classList.remove('hidden');
    }

    // ================= AI Q&A (Gemini 3.8 Flash) =================
    document.querySelectorAll('.qa-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        document.getElementById('input-qa-question').value = btn.getAttribute('data-q');
        document.getElementById('qa-form').dispatchEvent(new Event('submit'));
      });
    });

    document.getElementById('qa-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const question = document.getElementById('input-qa-question').value.trim();
      if (!question) return;

      if (!videoData || !currentVideoId) {
        alert('먼저 상단에서 유튜브 영상을 로드하고 전사가 완료될 때까지 기다려주세요.');
        return;
      }

      appendQAMessage('user', question);
      document.getElementById('input-qa-question').value = '';

      const loadingMsgId = appendQALoading();

      try {
        const res = await fetch('/api/qa', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            video_id: currentVideoId,
            question: question
          })
        });

        const data = await res.json();
        removeQALoading(loadingMsgId);

        if (!res.ok || !data.success) {
          throw new Error(data.detail || '답변 생성 실패');
        }

        appendQAMessage('ai', data.answer);

      } catch (err) {
        removeQALoading(loadingMsgId);
        appendQAMessage('ai', `답변 처리 중 문제가 발생했습니다: ${err.message}`);
      }
    });

    function appendQAMessage(sender, text) {
      const history = document.getElementById('qa-history');
      // 초기 안내문구 제거
      if (history.querySelector('.text-neutral-500')) {
        history.innerHTML = '';
      }

      const msgDiv = document.createElement('div');
      msgDiv.className = sender === 'user' ? 'flex justify-end' : 'flex justify-start';

      // 타임스탬프 링크 정규식 치환 [01:23] -> 클릭 가능한 태그
      const formattedText = text.replace(/\[(\d{1,2}:\d{2})\]/g, (match, timeStr) => {
        const parts = timeStr.split(':');
        const secs = parseInt(parts[0]) * 60 + parseInt(parts[1]);
        return `<button type="button" onclick="jumpAndPlay(${secs}, '${timeStr}', '타임스탬프 이동')" class="inline-flex items-center px-1.5 py-0.5 rounded bg-violet-500/20 text-violet-300 hover:bg-violet-500 hover:text-white font-mono text-xs mx-0.5 transition"><i class="fa-solid fa-play text-[9px] mr-1"></i>${timeStr}</button>`;
      });

      if (sender === 'user') {
        msgDiv.innerHTML = `
          <div class="chat-bubble-user max-w-lg bg-neutral-800 text-slate-100 px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm border border-neutral-700">
            ${escapeHtml(text)}
          </div>
        `;
      } else {
        msgDiv.innerHTML = `
          <div class="chat-bubble-ai max-w-xl bg-violet-950/40 border border-violet-800/40 text-slate-200 px-4 py-3 rounded-2xl rounded-tl-sm text-sm space-y-1.5 leading-relaxed">
            <div class="flex items-center space-x-1.5 text-xs text-violet-400 font-semibold mb-1">
              <i class="fa-solid fa-sparkles"></i>
              <span>Gemini AI</span>
            </div>
            <div class="whitespace-pre-wrap">${formattedText}</div>
          </div>
        `;
      }

      history.appendChild(msgDiv);
      history.scrollTop = history.scrollHeight;
    }

    function appendQALoading() {
      const history = document.getElementById('qa-history');
      const id = 'loading-' + Date.now();
      const div = document.createElement('div');
      div.id = id;
      div.className = 'flex justify-start';
      div.innerHTML = `
        <div class="chat-bubble-ai bg-violet-950/30 border border-violet-800/30 text-violet-300 px-4 py-2.5 rounded-2xl text-xs flex items-center space-x-2">
          <i class="fa-solid fa-circle-notch fa-spin"></i>
          <span>Gemini AI가 영상을 분석하여 답변을 작성하고 있습니다...</span>
        </div>
      `;
      history.appendChild(div);
      history.scrollTop = history.scrollHeight;
      return id;
    }

    function removeQALoading(id) {
      const elem = document.getElementById(id);
      if (elem) elem.remove();
    }

    function escapeHtml(string) {
      const div = document.createElement('div');
      div.innerText = string;
      return div.innerHTML;
    }

    // ================= Timeline Rendering =================
    function renderTimeline(segments) {
      const container = document.getElementById('timeline-container');
      container.innerHTML = '';
      if (!segments || segments.length === 0) {
        container.innerHTML = '<p class="text-xs text-neutral-500 py-6 text-center">세그먼트 데이터가 없습니다.</p>';
        return;
      }

      segments.forEach(seg => {
        const item = document.createElement('div');
        item.className = 'timeline-item flex items-start gap-3 p-2.5 rounded-xl bg-neutral-900/60 hover:bg-neutral-800/80 border border-neutral-800 transition group cursor-pointer';
        item.onclick = () => jumpAndPlay(seg.start_sec, seg.display_time, seg.text);
        item.innerHTML = `
          <button 
            type="button" 
            class="px-2 py-1 rounded bg-red-500/10 group-hover:bg-red-600 text-red-400 group-hover:text-white font-mono text-xs flex items-center space-x-1 flex-shrink-0 transition"
          >
            <i class="fa-solid fa-play text-[9px]"></i>
            <span>${seg.display_time}</span>
          </button>
          <div class="flex-1 min-w-0">
            <span class="text-[10px] text-neutral-500 font-semibold mr-1.5">${seg.speaker || 'spk:0'}</span>
            <span class="text-xs text-neutral-200 select-text">${escapeHtml(seg.text)}</span>
          </div>
        `;
        container.appendChild(item);
      });
    }

    // ================= Tabs Switching =================
    const tabs = [
      { btn: document.getElementById('tab-btn-qa'), panel: document.getElementById('tab-panel-qa') },
      { btn: document.getElementById('tab-btn-timeline'), panel: document.getElementById('tab-panel-timeline') },
    ];

    tabs.forEach(tab => {
      tab.btn.addEventListener('click', () => {
        tabs.forEach(t => {
          t.btn.className = 'tab-btn tab-btn-inactive px-4 py-2 rounded-lg text-xs font-semibold bg-neutral-800 text-neutral-400 hover:text-white transition flex items-center space-x-1.5';
          t.panel.classList.add('hidden');
        });
        tab.btn.className = 'tab-btn px-4 py-2 rounded-lg text-xs font-semibold bg-violet-600 text-white transition flex items-center space-x-1.5 shadow-sm';
        tab.panel.classList.remove('hidden');
      });
    });
