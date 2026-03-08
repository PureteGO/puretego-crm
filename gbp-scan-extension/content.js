/**
 * Maps2GO GBP Scan — Content Script
 * Injected into Google Search/Maps pages.
 * Listens for scan messages from popup and extracts business data from DOM.
 */

// Listen for scan trigger from popup
chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
    if (request.action !== 'scan') return;

    // Get config
    chrome.storage.local.get(['scan_token', 'server_url'], function (config) {
        if (!config.scan_token || !config.server_url) {
            sendResponse({ success: false, error: 'Token não configurado. Abra o popup da extensão.' });
            return;
        }

        try {
            const data = extractBusinessData();

            if (!data.business_name) {
                sendResponse({ success: false, error: 'Nenhum perfil de negócio detectado nesta página.' });
                return;
            }

            // Send to backend
            fetch(config.server_url + 'health-checks/api/gbp-scan/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + config.scan_token,
                },
                body: JSON.stringify(data),
            })
                .then(function (r) { return r.json(); })
                .then(function (result) {
                    if (result.success) {
                        sendResponse({
                            success: true,
                            score: result.score,
                            business_name: data.business_name,
                            check_id: result.check_id,
                        });
                        // Show floating notification on page
                        showPageNotification(result.score, data.business_name, config.server_url + 'health-checks/' + result.check_id);
                    } else {
                        sendResponse({ success: false, error: result.error || 'Erro do servidor.' });
                    }
                })
                .catch(function (err) {
                    sendResponse({ success: false, error: 'Erro de conexão: ' + err.message });
                });

        } catch (err) {
            sendResponse({ success: false, error: 'Erro na extração: ' + err.message });
        }
    });

    // Return true to keep the message channel open for async response
    return true;
});

// --- Data Extraction ---
function extractBusinessData() {
    const isMapPage = window.location.pathname.includes('/maps/');
    const pageType = isMapPage ? 'maps' : 'search';

    const biz = {
        page_type: pageType,
        scan_type: 'extension',
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
    // Business name
    const nameEl = document.querySelector('[data-attrid="title"] span') ||
        document.querySelector('.PZPZlf.ssJ7i span') ||
        document.querySelector('[data-attrid="title"]') ||
        document.querySelector('.SPZz6b h2 span') ||
        document.querySelector('.qrShPb span');
    biz.business_name = nameEl ? nameEl.textContent.trim() : '';

    // Rating
    const ratingEl = document.querySelector('.Aq14fc') || document.querySelector('.yi40Hd.YrbPuc');
    if (ratingEl) biz.rating = ratingEl.textContent.trim();

    // Reviews count
    const reviewsEl = document.querySelector('.hqzQac span') || document.querySelector('.z5jxId');
    if (reviewsEl) {
        const match = reviewsEl.textContent.match(/[\d.,]+/);
        if (match) biz.reviews_count = parseInt(match[0].replace(/[.,]/g, ''));
    }

    // Address
    const addrEl = document.querySelector('[data-attrid="kc:/location/location:address"] .LrzXr') ||
        document.querySelector('[data-local-attribute="d3adr"] .LrzXr') || document.querySelector('.LrzXr');
    if (addrEl) biz.address = addrEl.textContent.trim();

    // Phone
    const phoneEl = document.querySelector('[data-attrid*="phone"] .LrzXr') || document.querySelector('a[href^="tel:"]');
    if (phoneEl) biz.phone = phoneEl.textContent.trim();

    // Website
    const websiteEl = document.querySelector('[data-attrid*="official website"] a') || document.querySelector('a.n1obkb');
    if (websiteEl) biz.website = websiteEl.href || websiteEl.textContent.trim();

    // Category
    const catEl = document.querySelector('.YhemCb') || document.querySelector('.YDC0yf');
    if (catEl) biz.categories = [catEl.textContent.trim()];

    // Hours
    const hoursEl = document.querySelector('[data-attrid*="hours"] .LrzXr');
    if (hoursEl) biz.hours = hoursEl.textContent.trim();

    // Description
    const descEl = document.querySelector('[data-attrid="description"] span') ||
        document.querySelector('[data-attrid*="long_description"] span');
    if (descEl) biz.description = descEl.textContent.trim();

    // Verification
    biz.is_verified = !!document.querySelector('.QYOQwf');
    const bodyText = document.body.innerText.toLowerCase();
    if (bodyText.includes('não reivindicado') || bodyText.includes('no reclamado') || bodyText.includes('unclaimed')) {
        biz.is_verified = false;
    }

    // Photos
    const photoEls = document.querySelectorAll('[data-attrid*="lu attribute list"] img');
    biz.photo_count = photoEls.length;
    biz.has_photos = photoEls.length > 0;
    biz.has_logo = !!document.querySelector('img[alt*="logo" i]');

    // Posts
    biz.has_posts = !!document.querySelector('[data-attrid*="post"]') ||
        bodyText.includes('publicaciones') || bodyText.includes('atualizações');

    // Q&A
    biz.has_q_and_a = !!document.querySelector('[data-attrid*="question"]');

    // Review Responses
    biz.has_review_responses = document.querySelectorAll('.d6SCIc, .KYmsHe').length > 0;

    // Social
    biz.has_social_profiles = !!document.querySelector('[data-attrid*="social"]');

    // Products
    biz.has_products_services = !!document.querySelector('[data-attrid*="product"]') ||
        !!document.querySelector('[data-attrid*="menu"]') || !!document.querySelector('[data-attrid*="service"]');

    // CID
    const ludocid = document.querySelector('[data-ludocid]');
    if (ludocid) biz.cid = ludocid.getAttribute('data-ludocid');

    // Interior/exterior
    const imgTexts = Array.from(document.querySelectorAll('img')).map(i => (i.alt || '').toLowerCase()).join(' ');
    biz.has_interior_photos = imgTexts.includes('interior') || imgTexts.includes('inside');
    biz.has_exterior_photos = imgTexts.includes('exterior') || imgTexts.includes('fachada');
    biz.has_videos = !!document.querySelector('video') || imgTexts.includes('video');
}

function extractMapsData(biz) {
    // Business name
    const nameEl = document.querySelector('h1.DUwDvf') || document.querySelector('[role="main"] h1');
    biz.business_name = nameEl ? nameEl.textContent.trim() : '';

    // Rating
    const ratingEl = document.querySelector('.F7nice span[aria-hidden]');
    if (ratingEl) biz.rating = ratingEl.textContent.trim();

    // Reviews
    const reviewsEl = document.querySelector('.F7nice span[aria-label*="review"]') || document.querySelector('.F7nice + span');
    if (reviewsEl) {
        const match = reviewsEl.textContent.match(/[\d.,]+/);
        if (match) biz.reviews_count = parseInt(match[0].replace(/[.,]/g, ''));
    }

    // Category
    const catEl = document.querySelector('[jsaction*="category"] span') || document.querySelector('.DkEaL');
    if (catEl) biz.categories = [catEl.textContent.trim()];

    // Address
    const addrEl = document.querySelector('[data-item-id="address"] .Io6YTe');
    if (addrEl) biz.address = addrEl.textContent.trim();

    // Phone
    const phoneEl = document.querySelector('[data-item-id^="phone"] .Io6YTe');
    if (phoneEl) biz.phone = phoneEl.textContent.trim();

    // Website
    const websiteEl = document.querySelector('a[data-item-id="authority"]');
    if (websiteEl) biz.website = websiteEl.href || websiteEl.textContent.trim();

    // Hours
    const hoursEl = document.querySelector('[data-item-id="oh"] .Io6YTe');
    if (hoursEl) biz.hours = hoursEl.textContent.trim();

    // Verified
    biz.is_verified = !!document.querySelector('[aria-label*="Verified"]') ||
        !!document.querySelector('[aria-label*="verificado"]');

    // Photos
    const photoEls = document.querySelectorAll('[role="img"]');
    biz.photo_count = photoEls.length;
    biz.has_photos = photoEls.length > 0;

    // Tabs analysis
    const tabTexts = Array.from(document.querySelectorAll('[role="tab"]')).map(t => t.textContent.toLowerCase());
    biz.has_owner_photos = tabTexts.some(t => t.includes('owner') || t.includes('proprietário') || t.includes('propietario'));
    biz.has_interior_photos = tabTexts.some(t => t.includes('interior') || t.includes('inside'));
    biz.has_exterior_photos = tabTexts.some(t => t.includes('exterior') || t.includes('fachada'));
    biz.has_videos = tabTexts.some(t => t.includes('video') || t.includes('vídeo'));
    biz.has_posts = tabTexts.some(t => t.includes('update') || t.includes('post') || t.includes('publicación'));
    biz.has_products_services = tabTexts.some(t => t.includes('product') || t.includes('menu') || t.includes('service'));
    biz.has_q_and_a = tabTexts.some(t => t.includes('q&a') || t.includes('preguntas') || t.includes('perguntas'));

    // Review responses
    biz.has_review_responses = document.querySelectorAll('.CDe7pd').length > 0;

    // CID from URL
    const cidMatch = window.location.href.match(/[?&]cid=(\d+)/);
    if (cidMatch) biz.cid = cidMatch[1];

    // Place ID from URL
    const pidMatch = window.location.href.match(/place\/[^/]+\/([^/?]+)/);
    if (pidMatch) biz.place_id = pidMatch[1];

    // Coordinates
    const coordMatch = window.location.href.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
    if (coordMatch) biz.coordinates = { lat: parseFloat(coordMatch[1]), lng: parseFloat(coordMatch[2]) };

    // Logo
    biz.has_logo = !!document.querySelector('.aoRNLd img') || !!document.querySelector('[role="main"] img[src*="lh3"]');

    // Description
    const descEl = document.querySelector('.PYvSYb') || document.querySelector('[data-item-id="merchant_description"]');
    if (descEl) biz.description = descEl.textContent.trim();

    // Social
    biz.has_social_profiles = !!document.querySelector('[data-item-id*="social"]');
}

// --- Floating notification on the Google page ---
function showPageNotification(score, bizName, reportUrl) {
    const existing = document.getElementById('m2g-ext-notif');
    if (existing) existing.remove();

    const scoreColor = score > 70 ? '#00aa66' : score > 40 ? '#ffc107' : '#dc3545';

    const notif = document.createElement('div');
    notif.id = 'm2g-ext-notif';
    notif.innerHTML = `
        <div style="position:fixed;bottom:24px;right:24px;z-index:2147483647;background:#1a1a2e;border:2px solid ${scoreColor};border-radius:16px;padding:20px 24px;box-shadow:0 12px 40px rgba(0,0,0,0.4);max-width:320px;font-family:Inter,sans-serif;cursor:pointer;" onclick="window.open('${reportUrl}','_blank');this.parentElement.remove();">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                <div style="width:50px;height:50px;border-radius:50%;background:${scoreColor};display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:bold;color:white;">${score}</div>
                <div>
                    <div style="color:white;font-size:14px;font-weight:700;">Maps2GO Scan</div>
                    <div style="color:#888;font-size:12px;">${bizName}</div>
                </div>
            </div>
            <div style="color:#00aa66;font-size:11px;text-align:center;">Clique para ver relatório completo →</div>
            <div style="position:absolute;top:8px;right:12px;color:#555;font-size:18px;cursor:pointer;" onclick="event.stopPropagation();this.parentElement.parentElement.remove();">✕</div>
        </div>
    `;
    document.body.appendChild(notif);

    // Auto-remove after 15s
    setTimeout(function () {
        const el = document.getElementById('m2g-ext-notif');
        if (el) el.remove();
    }, 15000);
}
