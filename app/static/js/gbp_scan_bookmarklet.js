/**
 * Maps2GO GBP Scan — Bookmarklet
 * Extrai dados do Knowledge Panel do Google e envia para o backend.
 * Carregado via: javascript:void(function(){var s=document.createElement('script');s.src='URL?t=TOKEN&u=BASE';document.head.appendChild(s);}())
 */
(function () {
    'use strict';

    // --- Config (from URL params) ---
    const scriptTag = document.currentScript || document.querySelector('script[src*="gbp_scan_bookmarklet"]');
    const params = new URL(scriptTag.src).searchParams;
    const SCAN_TOKEN = params.get('t') || '';
    const API_BASE = (params.get('u') || '').replace(/\/$/, '');

    if (!SCAN_TOKEN || !API_BASE) {
        alert('Maps2GO Scan: Token ou URL não configurados. Acesse o setup no Maps2GO.');
        return;
    }

    // --- Check if on Google ---
    const isGoogle = window.location.hostname.includes('google.');
    if (!isGoogle) {
        alert('Maps2GO Scan: Abra esta ferramenta em uma página do Google Search ou Maps.');
        return;
    }

    // --- UI: Show scanning indicator ---
    const overlay = document.createElement('div');
    overlay.id = 'm2g-scan-overlay';
    overlay.innerHTML = `
        <div style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:2147483647;display:flex;align-items:center;justify-content:center;">
            <div style="background:#1a1a2e;border:2px solid #00aa66;border-radius:16px;padding:32px 48px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,0.5);max-width:400px;">
                <div style="width:48px;height:48px;border:4px solid #00aa66;border-top-color:transparent;border-radius:50%;animation:m2g-spin 1s linear infinite;margin:0 auto 16px;"></div>
                <div style="color:#00aa66;font-size:18px;font-weight:bold;font-family:Inter,sans-serif;">Maps2GO Scan</div>
                <div id="m2g-status" style="color:#ccc;font-size:13px;margin-top:8px;font-family:Inter,sans-serif;">Extraindo dados...</div>
            </div>
        </div>
        <style>@keyframes m2g-spin{to{transform:rotate(360deg)}}</style>
    `;
    document.body.appendChild(overlay);

    function updateStatus(msg) {
        const el = document.getElementById('m2g-status');
        if (el) el.textContent = msg;
    }

    function removeOverlay() {
        const el = document.getElementById('m2g-scan-overlay');
        if (el) el.remove();
    }

    function showResult(success, message) {
        const el = document.getElementById('m2g-scan-overlay');
        if (!el) return;
        const color = success ? '#00aa66' : '#dc3545';
        const icon = success ? '✅' : '❌';
        el.innerHTML = `
            <div style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:2147483647;display:flex;align-items:center;justify-content:center;" onclick="this.parentElement.remove()">
                <div style="background:#1a1a2e;border:2px solid ${color};border-radius:16px;padding:32px 48px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,0.5);max-width:450px;cursor:pointer;">
                    <div style="font-size:48px;margin-bottom:12px;">${icon}</div>
                    <div style="color:${color};font-size:18px;font-weight:bold;font-family:Inter,sans-serif;">${success ? 'Scan Concluído!' : 'Erro no Scan'}</div>
                    <div style="color:#ccc;font-size:13px;margin-top:8px;font-family:Inter,sans-serif;">${message}</div>
                    <div style="color:#888;font-size:11px;margin-top:16px;">Clique para fechar</div>
                </div>
            </div>
        `;
        if (success) setTimeout(() => removeOverlay(), 8000);
    }

    // --- Extract Data ---
    try {
        updateStatus('Identificando perfil...');
        const data = extractBusinessData();

        if (!data.business_name) {
            showResult(false, 'Nenhum perfil de negócio detectado nesta página. Pesquise um negócio e tente novamente.');
            return;
        }

        updateStatus('Enviando dados para Maps2GO...');
        sendToBackend(data);

    } catch (err) {
        console.error('Maps2GO Scan error:', err);
        showResult(false, 'Erro ao extrair dados: ' + err.message);
    }

    // --- Data Extraction Functions ---
    function extractBusinessData() {
        const isMapPage = window.location.pathname.includes('/maps/');
        const pageType = isMapPage ? 'maps' : 'search';

        // Common data object
        const biz = {
            page_type: pageType,
            scan_type: 'bookmarklet',
            url: window.location.href,
            business_name: '',
            address: '',
            phone: '',
            website: '',
            rating: null,
            reviews_count: 0,
            hours: null,
            categories: [],
            description: '',
            has_posts: false,
            has_photos: false,
            photo_count: 0,
            has_videos: false,
            has_logo: false,
            has_q_and_a: false,
            is_verified: false,
            has_owner_photos: false,
            has_review_responses: false,
            has_interior_photos: false,
            has_exterior_photos: false,
            has_social_profiles: false,
            has_products_services: false,
            cid: '',
            place_id: '',
            coordinates: null,
        };

        if (isMapPage) {
            extractMapsData(biz);
        } else {
            extractSearchData(biz);
        }

        return biz;
    }

    function extractSearchData(biz) {
        // --- Knowledge Panel on Search ---
        // Business name (multiple selectors for robustness)
        const nameEl = document.querySelector('[data-attrid="title"] span') ||
            document.querySelector('.PZPZlf.ssJ7i span') ||
            document.querySelector('[data-attrid="title"]') ||
            document.querySelector('.SPZz6b h2 span') ||
            document.querySelector('.qrShPb span');
        biz.business_name = nameEl ? nameEl.textContent.trim() : '';

        // Rating
        const ratingEl = document.querySelector('[data-attrid="kc:/local:lu attribute list"] .Aq14fc') ||
            document.querySelector('.Aq14fc') ||
            document.querySelector('.yi40Hd.YrbPuc');
        if (ratingEl) biz.rating = ratingEl.textContent.trim();

        // Reviews count
        const reviewsEl = document.querySelector('[data-attrid="kc:/local:lu attribute list"] .hqzQac span') ||
            document.querySelector('.hqzQac span') ||
            document.querySelector('.z5jxId');
        if (reviewsEl) {
            const match = reviewsEl.textContent.match(/[\d.,]+/);
            if (match) biz.reviews_count = parseInt(match[0].replace(/[.,]/g, ''));
        }

        // Address
        const addrEl = document.querySelector('[data-attrid="kc:/location/location:address"] .LrzXr') ||
            document.querySelector('[data-local-attribute="d3adr"] .LrzXr') ||
            document.querySelector('.LrzXr');
        if (addrEl) biz.address = addrEl.textContent.trim();

        // Phone
        const phoneEl = document.querySelector('[data-attrid="kc:/collection/knowledge_panels/has_phone:phone"] .LrzXr') ||
            document.querySelector('[data-local-attribute="d3ph"] .LrzXr') ||
            document.querySelector('a[href^="tel:"]');
        if (phoneEl) biz.phone = phoneEl.textContent.trim();

        // Website
        const websiteEl = document.querySelector('[data-attrid="kc:/common/topic:official website"] a') ||
            document.querySelector('a.n1obkb') ||
            document.querySelector('[data-dtype="d3ifr"] a');
        if (websiteEl) biz.website = websiteEl.href || websiteEl.textContent.trim();

        // Category
        const catEl = document.querySelector('.YhemCb') ||
            document.querySelector('.YDC0yf');
        if (catEl) biz.categories = [catEl.textContent.trim()];

        // Hours
        const hoursEl = document.querySelector('[data-attrid="kc:/location/location:hours"] .LrzXr') ||
            document.querySelector('[data-local-attribute="d3oh"]');
        if (hoursEl) biz.hours = hoursEl.textContent.trim();

        // Description
        const descEl = document.querySelector('[data-attrid="description"] span') ||
            document.querySelector('[data-attrid="kc:/location/location:long_description"] span') ||
            document.querySelector('.PZPZlf span.e24Kjd');
        if (descEl) biz.description = descEl.textContent.trim();

        // Verification
        const verifiedEl = document.querySelector('.QYOQwf') || // "Claimed" badge
            document.querySelector('[data-attrid*="verified"]');
        biz.is_verified = !!verifiedEl;
        // If there is NO "não reivindicado" text, likely verified
        const bodyText = document.body.innerText.toLowerCase();
        if (bodyText.includes('não reivindicado') || bodyText.includes('no reclamado') || bodyText.includes('unclaimed')) {
            biz.is_verified = false;
        }

        // Photos
        const photoEls = document.querySelectorAll('[data-attrid="kc:/local:lu attribute list"] img, .lu_map_section img');
        biz.photo_count = photoEls.length;
        biz.has_photos = photoEls.length > 0;
        biz.has_logo = !!document.querySelector('[data-attrid="kc:/local:lu attribute list"] img[alt*="logo" i]');

        // Posts
        biz.has_posts = !!document.querySelector('[data-attrid*="post"]') ||
            bodyText.includes('publicaciones') ||
            bodyText.includes('atualizações');

        // Q&A
        biz.has_q_and_a = !!document.querySelector('[data-attrid*="question"]') ||
            !!document.querySelector('[jscontroller*="question"]');

        // Review Responses (owner replies)
        const ownerReplies = document.querySelectorAll('.d6SCIc, .KYmsHe');
        biz.has_review_responses = ownerReplies.length > 0;

        // Social profiles
        biz.has_social_profiles = !!document.querySelector('[data-attrid*="social"]') ||
            !!document.querySelector('[data-attrid="kc:/common/topic:social media presence"]');

        // Products/services
        biz.has_products_services = !!document.querySelector('[data-attrid*="product"]') ||
            !!document.querySelector('[data-attrid*="menu"]') ||
            !!document.querySelector('[data-attrid*="service"]');

        // CID from different sources
        const ludocid = document.querySelector('[data-ludocid]');
        if (ludocid) biz.cid = ludocid.getAttribute('data-ludocid');

        // Interior/exterior from photo categories
        const allImgTexts = Array.from(document.querySelectorAll('img')).map(i => (i.alt || '').toLowerCase()).join(' ');
        biz.has_interior_photos = allImgTexts.includes('interior') || allImgTexts.includes('inside') || allImgTexts.includes('dentro');
        biz.has_exterior_photos = allImgTexts.includes('exterior') || allImgTexts.includes('fachada') || allImgTexts.includes('outside');

        // Videos
        biz.has_videos = !!document.querySelector('video') || allImgTexts.includes('video');
    }

    function extractMapsData(biz) {
        // --- Google Maps page ---
        // Business name
        const nameEl = document.querySelector('h1.DUwDvf') ||
            document.querySelector('[role="main"] h1') ||
            document.querySelector('.qBF1Pd.fontHeadlineSmall');
        biz.business_name = nameEl ? nameEl.textContent.trim() : '';

        // Rating
        const ratingEl = document.querySelector('.F7nice span[aria-hidden]') ||
            document.querySelector('.ceNzKf [aria-label*="star"]');
        if (ratingEl) biz.rating = ratingEl.textContent.trim();

        // Reviews
        const reviewsEl = document.querySelector('.F7nice span[aria-label*="review"]') ||
            document.querySelector('.F7nice + span');
        if (reviewsEl) {
            const match = reviewsEl.textContent.match(/[\d.,]+/);
            if (match) biz.reviews_count = parseInt(match[0].replace(/[.,]/g, ''));
        }

        // Category
        const catEl = document.querySelector('[jsaction*="pane.rating.category"] span') ||
            document.querySelector('.DkEaL');
        if (catEl) biz.categories = [catEl.textContent.trim()];

        // Address
        const addrEl = document.querySelector('[data-item-id="address"] .Io6YTe') ||
            document.querySelector('button[data-item-id="address"] .fontBodyMedium');
        if (addrEl) biz.address = addrEl.textContent.trim();

        // Phone
        const phoneEl = document.querySelector('[data-item-id^="phone"] .Io6YTe') ||
            document.querySelector('button[data-item-id^="phone"] .fontBodyMedium');
        if (phoneEl) biz.phone = phoneEl.textContent.trim();

        // Website
        const websiteEl = document.querySelector('a[data-item-id="authority"]') ||
            document.querySelector('[data-item-id="authority"] .Io6YTe');
        if (websiteEl) biz.website = websiteEl.href || websiteEl.textContent.trim();

        // Hours
        const hoursEl = document.querySelector('[data-item-id="oh"] .Io6YTe') ||
            document.querySelector('[aria-label*="hour"]');
        if (hoursEl) biz.hours = hoursEl.textContent.trim();

        // Verified
        const verifiedIcon = document.querySelector('.UY7F9 .google-symbols[aria-label*="Verified"]') ||
            document.querySelector('[aria-label*="verificado"]');
        biz.is_verified = !!verifiedIcon;

        // Photos count
        const photoBtns = document.querySelectorAll('[role="img"]');
        biz.photo_count = photoBtns.length;
        biz.has_photos = photoBtns.length > 0;

        // Owner photos
        const tabTexts = Array.from(document.querySelectorAll('[role="tab"]')).map(t => t.textContent.toLowerCase());
        biz.has_owner_photos = tabTexts.some(t => t.includes('owner') || t.includes('proprietário') || t.includes('propietario'));
        biz.has_interior_photos = tabTexts.some(t => t.includes('interior') || t.includes('inside') || t.includes('dentro'));
        biz.has_exterior_photos = tabTexts.some(t => t.includes('exterior') || t.includes('fachada'));
        biz.has_videos = tabTexts.some(t => t.includes('video') || t.includes('vídeo'));

        // Posts
        biz.has_posts = tabTexts.some(t => t.includes('update') || t.includes('post') || t.includes('publicación'));

        // Review responses
        const ownerReply = document.querySelectorAll('.CDe7pd');
        biz.has_review_responses = ownerReply.length > 0;

        // Products/services
        biz.has_products_services = tabTexts.some(t => t.includes('product') || t.includes('menu') || t.includes('service'));

        // CID from URL
        const cidMatch = window.location.href.match(/[?&]cid=(\d+)/);
        if (cidMatch) biz.cid = cidMatch[1];

        // Place ID from URL
        const pidMatch = window.location.href.match(/place\/[^/]+\/([^/?]+)/);
        if (pidMatch) biz.place_id = pidMatch[1];

        // Coordinates from URL
        const coordMatch = window.location.href.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
        if (coordMatch) {
            biz.coordinates = { lat: parseFloat(coordMatch[1]), lng: parseFloat(coordMatch[2]) };
        }

        // Logo
        biz.has_logo = !!document.querySelector('.aoRNLd img') || !!document.querySelector('[role="main"] img[src*="lh3"]');

        // Description
        const descEl = document.querySelector('.PYvSYb') ||
            document.querySelector('[data-item-id="merchant_description"]');
        if (descEl) biz.description = descEl.textContent.trim();

        // Social profiles
        biz.has_social_profiles = !!document.querySelector('[data-item-id*="social"]');

        // Q&A
        biz.has_q_and_a = tabTexts.some(t => t.includes('q&a') || t.includes('preguntas') || t.includes('perguntas'));
    }

    // --- Send to Backend ---
    function sendToBackend(data) {
        fetch(API_BASE + 'health-checks/api/gbp-scan/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + SCAN_TOKEN,
            },
            body: JSON.stringify(data),
        })
            .then(function (response) { return response.json(); })
            .then(function (result) {
                if (result.success) {
                    const score = result.score || 0;
                    const reportUrl = API_BASE + 'health-checks/' + result.check_id;
                    showResult(true,
                        'Score: ' + score + '/100\n' +
                        'Negócio: ' + (data.business_name || '-') + '\n\n' +
                        'Relatório salvo no Maps2GO.'
                    );
                } else {
                    showResult(false, result.error || 'Erro desconhecido');
                }
            })
            .catch(function (err) {
                console.error('Maps2GO Scan send error:', err);
                showResult(false, 'Erro de conexão com o servidor. Verifique se o Maps2GO está acessível.');
            });
    }

})();
