from pathlib import Path

ROOT = Path('/home/ubuntu/baakbook-local/frontend')
INDEX = ROOT / 'index.html'
ADMIN = ROOT / 'admin.html'

index = INDEX.read_text()
admin = ADMIN.read_text()

old_css = '''/* HERO */
.hero{margin-top:var(--nav-height);padding:76px 24px 34px;text-align:center;position:relative;overflow:hidden}
.hero::before{content:'';position:absolute;top:-60%;left:12%;width:76%;height:120%;background:radial-gradient(ellipse at center,rgba(196,151,90,0.14) 0%,transparent 68%);pointer-events:none}
.hero-orbit{position:absolute;border:1px solid rgba(196,151,90,.16);border-radius:50%;pointer-events:none}
.hero-orbit-one{width:420px;height:220px;top:58px;left:50%;transform:translateX(-50%) rotate(-8deg)}
.hero-orbit-two{width:620px;height:310px;top:24px;left:50%;transform:translateX(-50%) rotate(10deg);border-color:rgba(196,151,90,.08)}
.hero-content{position:relative;z-index:1;max-width:760px;margin:0 auto}
.hero-kicker{display:inline-block;padding:5px 13px;border-radius:999px;background:rgba(196,151,90,.12);color:var(--accent-dark);font-size:11px;font-weight:800;margin-bottom:14px}
.hero h1{font-size:46px;font-weight:800;letter-spacing:-.7px;margin-bottom:12px;position:relative}
.hero h1 span{color:var(--accent)}
.hero p{font-size:17px;color:var(--text-secondary);max-width:560px;margin:0 auto 28px;position:relative}
.hero-actions{display:flex;justify-content:center;gap:10px;flex-wrap:wrap;position:relative}
.hero-secondary-cta{background:var(--accent)!important}
.hero-feature-rail{position:relative;z-index:1;display:grid;grid-template-columns:repeat(4,1fr);gap:10px;max-width:960px;margin:38px auto 0;padding:10px;border:1px solid rgba(196,151,90,.18);border-radius:22px;background:rgba(255,255,255,.52);box-shadow:0 12px 34px rgba(0,0,0,.05);backdrop-filter:blur(14px)}
.hero-feature-card{display:flex;align-items:center;gap:10px;text-align:right;padding:13px;border:1px solid transparent;border-radius:15px;background:rgba(255,255,255,.58);transition:transform .2s,border-color .2s,background .2s}
.hero-feature-card:hover{transform:translateY(-2px);border-color:rgba(196,151,90,.45);background:rgba(255,255,255,.85)}
.hero-feature-icon{width:32px;height:32px;flex:0 0 32px;display:flex;align-items:center;justify-content:center;border-radius:10px;background:var(--accent-light);color:var(--accent-dark);font-size:16px}
.hero-feature-card strong,.hero-feature-card small{display:block}.hero-feature-card strong{font-size:12px}.hero-feature-card small{font-size:10px;color:var(--text-secondary);margin-top:2px}
.hero[hidden],.feature-hub[hidden],.hero-feature-rail[hidden],[data-feature][hidden]{display:none!important}
.feature-visibility-pending [data-feature],.feature-visibility-pending [data-feature-group]{display:none!important}
'''

new_css = '''/* HERO SLIDER — Baak Books adaptation of the Afak Carpet interaction model */
.hero{margin-top:var(--nav-height);padding:18px 24px 34px;position:relative;overflow:hidden}
.hero-slider{position:relative;max-width:var(--max-width);min-height:540px;margin:0 auto;border-radius:30px;overflow:hidden;background:#26221e;box-shadow:0 24px 70px rgba(29,29,31,.14)}
.hero-slide{position:absolute;inset:0;display:grid;align-items:center;opacity:0;visibility:hidden;transform:scale(1.018);transition:opacity .55s ease,transform .8s ease,visibility .55s;isolation:isolate}
.hero-slide.active{opacity:1;visibility:visible;transform:scale(1)}
.hero-slide-media,.hero-slide-shade,.hero-slide-reflection{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;pointer-events:none}
.hero-slide-media{z-index:-3}
.hero-slide-shade{z-index:-2;background:linear-gradient(90deg,rgba(20,17,14,.78) 0%,rgba(20,17,14,.48) 42%,rgba(20,17,14,.16) 100%)}
.hero-slide-reflection{z-index:-1;background:linear-gradient(180deg,rgba(255,255,255,.18),transparent 32%);opacity:0}
.hero-slide.has-reflection .hero-slide-reflection{opacity:1}
.hero-slide-copy{width:min(650px,72%);padding:70px 76px;color:var(--hero-text,#fff);text-align:right;text-shadow:var(--hero-text-shadow,none)}
.hero-slide-eyebrow{display:inline-flex;align-items:center;gap:8px;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;margin-bottom:14px;color:inherit;opacity:.9}
.hero-slide-eyebrow::before{content:'';width:28px;height:2px;background:var(--accent);border-radius:9px}
.hero-slide h1{font-size:clamp(32px,5vw,64px);font-weight:800;line-height:1.2;letter-spacing:-1.1px;margin-bottom:14px;color:inherit}
.hero-slide p{max-width:570px;font-size:clamp(14px,1.7vw,18px);line-height:1.9;margin-bottom:28px;color:inherit;opacity:.9}
.hero-actions{display:flex;justify-content:flex-start;gap:10px;flex-wrap:wrap;position:relative}
.hero-slide-cta{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:10px 20px;border-radius:14px;font-size:13px;font-weight:800;text-decoration:none;transition:transform .2s,background .2s,box-shadow .2s;border:1px solid transparent}
.hero-slide-cta:hover{transform:translateY(-2px)}
.hero-slide-cta.primary{background:var(--accent);color:#fff;box-shadow:0 12px 26px rgba(0,0,0,.18)}
.hero-slide-cta.primary:hover{background:var(--accent-dark)}
.hero-slide-cta.secondary{background:rgba(255,255,255,.14);border-color:rgba(255,255,255,.5);color:inherit;backdrop-filter:blur(10px)}
.hero-slide-cta.secondary:hover{background:rgba(255,255,255,.26)}
.hero-slider-control{position:absolute;z-index:3;top:50%;width:42px;height:42px;display:flex;align-items:center;justify-content:center;border-radius:50%;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.35);color:#fff;font-size:22px;transform:translateY(-50%);backdrop-filter:blur(10px);transition:background .2s,transform .2s}
.hero-slider-control:hover{background:rgba(255,255,255,.28);transform:translateY(-50%) scale(1.05)}
.hero-slider-control.prev{right:22px}.hero-slider-control.next{left:22px}
.hero-dots{position:absolute;z-index:3;bottom:22px;left:50%;display:flex;gap:7px;transform:translateX(-50%)}
.hero-dot{width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,.46);transition:width .25s,background .25s}.hero-dot.active{width:25px;border-radius:8px;background:var(--accent)}
.hero-scroll-hint{position:absolute;z-index:3;bottom:18px;right:28px;color:rgba(255,255,255,.78);font-size:10px;display:flex;align-items:center;gap:8px}.hero-scroll-hint::after{content:'↓';font-size:16px;color:var(--accent)}
.hero-feature-rail{position:relative;z-index:4;display:grid;grid-template-columns:repeat(4,1fr);gap:10px;max-width:960px;margin:18px auto 0;padding:10px;border:1px solid rgba(196,151,90,.18);border-radius:22px;background:rgba(255,255,255,.52);box-shadow:0 12px 34px rgba(0,0,0,.05);backdrop-filter:blur(14px)}
.hero-feature-card{display:flex;align-items:center;gap:10px;text-align:right;padding:13px;border:1px solid transparent;border-radius:15px;background:rgba(255,255,255,.58);transition:transform .2s,border-color .2s,background .2s}.hero-feature-card:hover{transform:translateY(-2px);border-color:rgba(196,151,90,.45);background:rgba(255,255,255,.85)}
.hero-feature-icon{width:32px;height:32px;flex:0 0 32px;display:flex;align-items:center;justify-content:center;border-radius:10px;background:var(--accent-light);color:var(--accent-dark);font-size:16px}.hero-feature-card strong,.hero-feature-card small{display:block}.hero-feature-card strong{font-size:12px}.hero-feature-card small{font-size:10px;color:var(--text-secondary);margin-top:2px}
.hero[hidden],.feature-hub[hidden],.hero-feature-rail[hidden],[data-feature][hidden]{display:none!important}.feature-visibility-pending [data-feature],.feature-visibility-pending [data-feature-group]{display:none!important}
@media(max-width:760px){.hero{padding:10px 12px 24px}.hero-slider{min-height:570px;border-radius:24px}.hero-slide-copy{width:100%;padding:42px 28px 70px;text-align:center}.hero-slide-eyebrow{justify-content:center}.hero-slide h1{font-size:36px}.hero-slide p{font-size:14px;margin-left:auto;margin-right:auto}.hero-actions{justify-content:center}.hero-slider-control{width:36px;height:36px}.hero-slider-control.prev{right:12px}.hero-slider-control.next{left:12px}.hero-scroll-hint{right:50%;transform:translateX(50%);bottom:48px}.hero-feature-rail{grid-template-columns:repeat(2,1fr);margin-top:12px}.hero-feature-card{padding:10px}.hero-feature-card strong{font-size:11px}.hero-feature-card small{font-size:9px}}
'''
if old_css not in index:
    raise SystemExit('old hero CSS block not found')
index = index.replace(old_css, new_css, 1)

old_html = '''<section class="hero" id="storefrontHero" aria-labelledby="heroTitle">
  <div class="hero-orbit hero-orbit-one" aria-hidden="true"></div>
  <div class="hero-orbit hero-orbit-two" aria-hidden="true"></div>
  <div class="hero-content">
    <span class="hero-kicker">مكتبة Baak Books</span>
    <h1 id="heroTitle">كتابك <span>القادم</span> يبدأ من هنا</h1>
    <p id="heroSubtitle">كتب وروايات اخترناها بعناية؛ لأن الكتاب المناسب لا يملأ وقتك فقط، بل يترك فيك أثرًا.</p>
    <div class="hero-actions" id="heroActions">
      <button class="discover-cta" id="heroDiscoverOpen" data-feature="discovery"><span class="spark">✦</span><span id="heroPrimaryLabel">اكتشف كتابك القادم</span></button>
      <button class="discover-cta hero-secondary-cta" id="heroGiftOpen" data-feature="gifts" data-feature-requires="gift_finder"><span class="spark">◈</span><span id="heroSecondaryLabel">اختر هدية تحمل معنى</span></button>
    </div>
  </div>
  <div class="hero-feature-rail" id="heroFeatureRail" data-feature-group aria-label="مسارات القراءة">
    <button class="hero-feature-card" id="heroRailDiscover" data-feature="discovery" type="button"><span class="hero-feature-icon">✦</span><span><strong>اكتشف كتابك</strong><small>اختيارات تناسب ذوقك الآن</small></span></button>
    <button class="hero-feature-card" id="heroRailGift" data-feature="gifts" data-feature-requires="gift_finder" type="button"><span class="hero-feature-icon">🎁</span><span><strong>اصنع هدية</strong><small>كتاب يحمل معنى لمن تحب</small></span></button>
    <button class="hero-feature-card" id="heroRailOnDemand" data-feature="on_demand" type="button"><span class="hero-feature-icon">⌛</span><span><strong>كتب يمكن اقتناؤها</strong><small>عناوين تصل في اليوم نفسه أو خلال يوم</small></span></button>
    <button class="hero-feature-card" id="heroRailLab" data-feature="ideas_lab" type="button"><span class="hero-feature-icon">◈</span><span><strong>مختبر الأفكار</strong><small>مسارات جديدة لاكتشاف القراءة</small></span></button>
  </div>
</section>'''

new_html = '''<section class="hero" id="storefrontHero" aria-label="الواجهة الرئيسية">
  <div class="hero-slider" id="heroSlider" aria-live="polite">
    <div id="heroSlides" class="hero-slides"></div>
    <button class="hero-slider-control prev" id="heroPrev" type="button" aria-label="الشريحة السابقة">‹</button>
    <button class="hero-slider-control next" id="heroNext" type="button" aria-label="الشريحة التالية">›</button>
    <div class="hero-dots" id="heroDots" role="tablist" aria-label="مؤشرات الشرائح"></div>
    <div class="hero-scroll-hint" id="heroScrollHint">مرّر لاكتشاف الكتب</div>
  </div>
  <div class="hero-feature-rail" id="heroFeatureRail" data-feature-group aria-label="مسارات القراءة">
    <button class="hero-feature-card" id="heroRailDiscover" data-feature="discovery" type="button"><span class="hero-feature-icon">✦</span><span><strong>اكتشف كتابك</strong><small>اختيارات تناسب ذوقك الآن</small></span></button>
    <button class="hero-feature-card" id="heroRailGift" data-feature="gifts" data-feature-requires="gift_finder" type="button"><span class="hero-feature-icon">🎁</span><span><strong>اصنع هدية</strong><small>كتاب يحمل معنى لمن تحب</small></span></button>
    <button class="hero-feature-card" id="heroRailOnDemand" data-feature="on_demand" type="button"><span class="hero-feature-icon">⌛</span><span><strong>كتب يمكن اقتناؤها</strong><small>عناوين تصل في اليوم نفسه أو خلال يوم</small></span></button>
    <button class="hero-feature-card" id="heroRailLab" data-feature="ideas_lab" type="button"><span class="hero-feature-icon">◈</span><span><strong>مختبر الأفكار</strong><small>مسارات جديدة لاكتشاف القراءة</small></span></button>
  </div>
</section>'''
if old_html not in index:
    raise SystemExit('old hero HTML block not found')
index = index.replace(old_html, new_html, 1)

old_state = "let storefrontSettings = { hero: { visible: true, title: 'كتابك القادم يبدأ من هنا', subtitle: 'كتب وروايات اخترناها بعناية؛ لأن الكتاب المناسب لا يملأ وقتك فقط، بل يترك فيك أثرًا.', primary_cta_visible: true, primary_cta_label: 'اكتشف كتابك القادم', secondary_cta_visible: true, secondary_cta_label: 'اختر هدية تحمل معنى', feature_rail_visible: true } };"
new_state = '''const DEFAULT_HERO_SLIDES = [{
  id: 'default-baak-hero', active: true, image: 'https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?auto=format&fit=crop&w=1800&q=85',
  image_alt: 'كتب مفتوحة على طاولة', eyebrow: 'Baak Books', eyebrow_en: '', title: 'كتابك القادم يبدأ من هنا', title_en: '',
  text: 'كتب وروايات اخترناها بعناية؛ لأن الكتاب المناسب لا يملأ وقتك فقط، بل يترك فيك أثرًا.', text_en: '',
  primary_visible: true, primary_label: 'اكتشف كتابك القادم', primary_label_en: '', primary_action: 'discovery', primary_link: '',
  secondary_visible: true, secondary_label: 'اختر هدية تحمل معنى', secondary_label_en: '', secondary_action: 'gift', secondary_link: '',
  reflection: true, text_backdrop: true, text_color_mode: 'manual', text_color: '#ffffff', auto_text_color: '#ffffff'
}];
let heroTimer = null;
let heroIndex = 0;
let heroSlides = [...DEFAULT_HERO_SLIDES];
let storefrontSettings = { hero: { visible: true, autoplay: true, interval: 6, dots: true, arrows: true, scroll_hint: true, scroll_hint_label: 'مرّر لاكتشاف الكتب', height: 540, pause_on_interaction: true, feature_rail_visible: true, slides: [...DEFAULT_HERO_SLIDES] } };'''
if old_state not in index:
    raise SystemExit('old storefront state not found')
index = index.replace(old_state, new_state, 1)

old_apply = '''function applyHeroSettings() {
  const hero = $('storefrontHero');
  const config = { ...storefrontSettings.hero };
  if (!hero) return;
  hero.hidden = config.visible === false;
  if ($('heroTitle') && config.title) {
    const parts = String(config.title).split(' ');
    const accentIndex = parts.findIndex(part => /القادم|القراءة|كتاب/.test(part));
    $('heroTitle').textContent = config.title;
    if (accentIndex >= 0) {
      const title = String(config.title);
      const accentWord = parts[accentIndex];
      const start = title.indexOf(accentWord);
      if (start >= 0) $('heroTitle').innerHTML = `${esc(title.slice(0, start))}<span>${esc(accentWord)}</span>${esc(title.slice(start + accentWord.length))}`;
    }
  }
  if ($('heroSubtitle') && config.subtitle) $('heroSubtitle').textContent = config.subtitle;
  const primary = $('heroDiscoverOpen');
  const secondary = $('heroGiftOpen');
  if (primary) { primary.hidden = config.primary_cta_visible === false || !isFeatureElementEnabled(primary); if ($('heroPrimaryLabel') && config.primary_cta_label) $('heroPrimaryLabel').textContent = config.primary_cta_label; }
  if (secondary) { secondary.hidden = config.secondary_cta_visible === false || !isFeatureElementEnabled(secondary); if ($('heroSecondaryLabel') && config.secondary_cta_label) $('heroSecondaryLabel').textContent = config.secondary_cta_label; }
  if ($('heroFeatureRail')) $('heroFeatureRail').hidden = config.feature_rail_visible === false || !$qsaVisible('[data-feature]', $('heroFeatureRail'));
}
'''
new_apply = '''function normalizeHeroConfig(raw = {}) {
  const slides = Array.isArray(raw.slides) && raw.slides.length ? raw.slides : DEFAULT_HERO_SLIDES;
  return { visible: true, autoplay: true, interval: 6, dots: true, arrows: true, scroll_hint: true, scroll_hint_label: 'مرّر لاكتشاف الكتب', height: 540, pause_on_interaction: true, feature_rail_visible: true, ...raw, slides };
}
function heroActionLink(action, link) {
  if (action === 'discovery' || action === 'gift' || action === 'on_demand' || action === 'ideas_lab') return '#';
  const value = String(link || '#books').trim();
  return /^(https?:|mailto:|tel:|#|\/)/i.test(value) ? value : '#books';
}
function renderHeroSlides(config) {
  const slider = $('heroSlider'); const list = $('heroSlides'); const dots = $('heroDots');
  if (!slider || !list || !dots) return;
  heroSlides = (Array.isArray(config.slides) ? config.slides : []).filter(slide => slide && slide.active !== false);
  if (!heroSlides.length) heroSlides = [...DEFAULT_HERO_SLIDES];
  heroIndex = Math.min(heroIndex, heroSlides.length - 1);
  slider.style.minHeight = `${Math.max(420, Math.min(760, Number(config.height) || 540))}px`;
  list.innerHTML = heroSlides.map((slide, index) => {
    const color = /^#[0-9a-f]{6}$/i.test(String(slide.text_color || '')) ? slide.text_color : '#ffffff';
    const primaryAction = slide.primary_action || (slide.primary_link ? 'link' : 'discovery');
    const secondaryAction = slide.secondary_action || (slide.secondary_link ? 'link' : 'gift');
    const primaryFeature = primaryAction === 'discovery' ? ' data-feature="discovery"' : '';
    const secondaryFeature = secondaryAction === 'gift' ? ' data-feature="gifts" data-feature-requires="gift_finder"' : '';
    const primary = slide.primary_visible !== false && slide.primary_label ? `<a class="hero-slide-cta primary hero-action" data-hero-action="${esc(primaryAction)}" href="${esc(heroActionLink(primaryAction, slide.primary_link))}"${primaryFeature}>${esc(slide.primary_label)}</a>` : '';
    const secondary = slide.secondary_visible !== false && slide.secondary_label ? `<a class="hero-slide-cta secondary hero-action" data-hero-action="${esc(secondaryAction)}" href="${esc(heroActionLink(secondaryAction, slide.secondary_link))}"${secondaryFeature}>${esc(slide.secondary_label)}</a>` : '';
    return `<article class="hero-slide ${index === heroIndex ? 'active' : ''} ${slide.reflection ? 'has-reflection' : ''}" data-slide-index="${index}" aria-hidden="${index === heroIndex ? 'false' : 'true'}" style="--hero-text:${color};--hero-text-shadow:${slide.text_backdrop ? '0 2px 18px rgba(0,0,0,.34)' : 'none'}"><img class="hero-slide-media" src="${esc(slide.image || '')}" alt="${esc(slide.image_alt || slide.title || 'صورة Hero')}" loading="${index === 0 ? 'eager' : 'lazy'}"><div class="hero-slide-shade"></div><div class="hero-slide-reflection" aria-hidden="true"></div><div class="hero-slide-copy"><div class="hero-slide-eyebrow">${esc(slide.eyebrow || '')}</div><h1>${esc(slide.title || '')}</h1><p>${esc(slide.text || '')}</p><div class="hero-actions">${primary}${secondary}</div></div></article>`;
  }).join('');
  dots.innerHTML = heroSlides.length > 1 && config.dots !== false ? heroSlides.map((slide, index) => `<button class="hero-dot ${index === heroIndex ? 'active' : ''}" type="button" data-hero-dot="${index}" role="tab" aria-label="الشريحة ${index + 1}" aria-selected="${index === heroIndex}"></button>`).join('') : '';
  $('heroPrev').hidden = config.arrows === false || heroSlides.length < 2;
  $('heroNext').hidden = config.arrows === false || heroSlides.length < 2;
  $('heroScrollHint').hidden = config.scroll_hint === false;
  $('heroScrollHint').textContent = config.scroll_hint_label || 'مرّر لاكتشاف الكتب';
  updateHeroSlideState();
  startHeroAutoplay(config);
}
function updateHeroSlideState() {
  qsa('.hero-slide', $('heroSlider')).forEach((slide, index) => { const active = index === heroIndex; slide.classList.toggle('active', active); slide.setAttribute('aria-hidden', String(!active)); });
  qsa('.hero-dot', $('heroDots')).forEach((dot, index) => { const active = index === heroIndex; dot.classList.toggle('active', active); dot.setAttribute('aria-selected', String(active)); });
}
function setHeroSlide(next, restart = true) { if (!heroSlides.length) return; heroIndex = (next + heroSlides.length) % heroSlides.length; updateHeroSlideState(); if (restart) startHeroAutoplay(storefrontSettings.hero); }
function stopHeroAutoplay() { if (heroTimer) { clearInterval(heroTimer); heroTimer = null; } }
function startHeroAutoplay(config = storefrontSettings.hero) { stopHeroAutoplay(); if (config.autoplay === false || heroSlides.length < 2) return; const seconds = Math.max(2, Math.min(60, Number(config.interval) || 6)); heroTimer = setInterval(() => setHeroSlide(heroIndex + 1, false), seconds * 1000); }
function applyHeroSettings() {
  const hero = $('storefrontHero');
  const config = normalizeHeroConfig(storefrontSettings.hero || {});
  storefrontSettings.hero = config;
  if (!hero) return;
  hero.hidden = config.visible === false;
  renderHeroSlides(config);
  if ($('heroFeatureRail')) $('heroFeatureRail').hidden = config.feature_rail_visible === false || !$qsaVisible('[data-feature]', $('heroFeatureRail'));
  applyFeatureVisibility();
}
'''
if old_apply not in index:
    raise SystemExit('old applyHeroSettings block not found')
index = index.replace(old_apply, new_apply, 1)

old_handlers = '''$('heroRailLab').onclick = openLab;
$('labOpenHub').onclick = openLab;
$('heroRailDiscover').onclick = openDiscovery;
$('heroDiscoverOpen').onclick = openDiscovery;
$('discoverOpenHub').onclick = openDiscovery;
$('heroRailGift').onclick = openGiftBuilder;
$('heroGiftOpen').onclick = openGiftBuilder;
$('giftOpen').onclick = openGiftBuilder;
'''
new_handlers = '''$('heroRailLab').onclick = openLab;
$('labOpenHub').onclick = openLab;
$('heroRailDiscover').onclick = openDiscovery;
$('discoverOpenHub').onclick = openDiscovery;
$('heroRailGift').onclick = openGiftBuilder;
$('giftOpen').onclick = openGiftBuilder;
document.addEventListener('click', event => {
  const dot = event.target.closest('[data-hero-dot]');
  if (dot) { setHeroSlide(Number(dot.dataset.heroDot)); return; }
  if (event.target.closest('#heroPrev')) { setHeroSlide(heroIndex - 1); return; }
  if (event.target.closest('#heroNext')) { setHeroSlide(heroIndex + 1); return; }
  const action = event.target.closest('.hero-action');
  if (!action) return;
  const name = action.dataset.heroAction;
  if (name === 'discovery') { event.preventDefault(); openDiscovery(); }
  else if (name === 'gift') { event.preventDefault(); openGiftBuilder(); }
  else if (name === 'on_demand') { event.preventDefault(); $('heroRailOnDemand').click(); }
  else if (name === 'ideas_lab') { event.preventDefault(); openLab(); }
});
$('heroSlider').addEventListener('mouseenter', () => { if (storefrontSettings.hero.pause_on_interaction !== false) stopHeroAutoplay(); });
$('heroSlider').addEventListener('mouseleave', () => startHeroAutoplay(storefrontSettings.hero));
$('heroSlider').addEventListener('focusin', () => { if (storefrontSettings.hero.pause_on_interaction !== false) stopHeroAutoplay(); });
$('heroSlider').addEventListener('focusout', () => startHeroAutoplay(storefrontSettings.hero));
'''
if old_handlers not in index:
    raise SystemExit('old hero handlers not found')
index = index.replace(old_handlers, new_handlers, 1)

INDEX.write_text(index)

# Admin: CSS for the independent Hero editor.
admin_css_marker = '    @media(max-width:760px){.hero-settings-grid,.hero-copy-grid,.hero-cta-grid{grid-template-columns:1fr}}\n'
admin_css_add = '''    .hero-admin-settings,.hero-slide-form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.hero-slide-card{margin-top:16px;padding:18px;border:1px solid rgba(196,151,90,.22);border-radius:var(--radius-lg);background:rgba(255,255,255,.48)}.hero-slide-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:14px;flex-wrap:wrap}.hero-slide-head h3{font-size:15px}.hero-slide-order{display:flex;gap:6px}.hero-slide-order button{padding:5px 8px;border-radius:9px;background:rgba(0,0,0,.05);font-size:11px}.hero-slide-preview{width:100%;height:150px;object-fit:cover;border-radius:14px;background:#ece7df;margin-top:6px}.hero-slide-form .wide{grid-column:1/-1}.hero-slide-form input,.hero-slide-form select,.hero-slide-form textarea{width:100%;padding:9px 12px;border-radius:var(--radius-md);border:1px solid rgba(0,0,0,.1);background:rgba(255,255,255,.7);font-family:var(--font);font-size:13px}.hero-slide-form textarea{min-height:82px;resize:vertical}.hero-check{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:600;padding:9px 0}.hero-check input{width:auto!important}.danger-outline{border:1px solid var(--danger)!important;color:var(--danger)!important;background:transparent!important}.hero-empty{padding:24px;border:1px dashed rgba(0,0,0,.15);border-radius:var(--radius-md);color:var(--text-secondary);text-align:center}.hero-admin-note{padding:12px 14px;border-radius:var(--radius-md);background:rgba(196,151,90,.1);color:var(--accent-dark);font-size:12px;line-height:1.7;margin-bottom:16px}@media(max-width:760px){.hero-admin-settings,.hero-slide-form{grid-template-columns:1fr}.hero-slide-form .wide{grid-column:auto}}
'''
if admin_css_marker not in admin:
    raise SystemExit('admin css marker not found')
admin = admin.replace(admin_css_marker, admin_css_marker + admin_css_add, 1)

# Add independent tab.
old_tabs = '''        <button class="tab active" data-tab="products">📚 إدارة الكتب</button>
        <button class="tab" data-tab="orders">📦 الطلبات</button>'''
new_tabs = '''        <button class="tab active" data-tab="products">📚 إدارة الكتب</button>
        <button class="tab" data-tab="hero">🎞️ إدارة الـHero</button>
        <button class="tab" data-tab="orders">📦 الطلبات</button>'''
if old_tabs not in admin:
    raise SystemExit('admin tabs marker not found')
admin = admin.replace(old_tabs, new_tabs, 1)

# Add panel before orders.
panel_marker = '''      <!-- قسم الطلبات -->
      <div class="panel" id="panel-orders">'''
hero_panel = '''      <!-- إدارة الـHero -->
      <div class="panel" id="panel-hero">
        <div class="card">
          <h2 style="font-size:20px; margin-bottom:6px;">إدارة الـHero</h2>
          <p class="feature-intro">هذا القسم مستقل عن «ميزات المتجر». يمكنك هنا بناء شرائح متعددة، ترتيبها، والتحكم في كل تفاصيل العرض كما في نموذج السلايدر المرجعي.</p>
          <div class="hero-admin-note"><strong>منطق الحفظ:</strong> إيقاف الـHero يخفيه فقط ولا يحذف الشرائح. إيقاف شريحة يستبعدها من العرض دون حذفها. كل التغييرات تُحفظ في إعدادات الموقع العامة ولا تمس الكتب أو الطلبات.</div>
          <div class="hero-admin-settings">
            <label class="hero-check"><input type="checkbox" id="heroAdminVisible"> إظهار الـHero كاملًا</label>
            <label class="hero-check"><input type="checkbox" id="heroAdminAutoplay"> تشغيل التبديل التلقائي</label>
            <label class="hero-check"><input type="checkbox" id="heroAdminDots"> إظهار مؤشرات الشرائح</label>
            <label class="hero-check"><input type="checkbox" id="heroAdminArrows"> إظهار أسهم التنقل</label>
            <label class="hero-check"><input type="checkbox" id="heroAdminScrollHint"> إظهار تلميح التمرير</label>
            <label class="hero-check"><input type="checkbox" id="heroAdminPause"> إيقاف التبديل عند التفاعل</label>
            <div class="form-group"><label>مدة التبديل (بالثواني)</label><input type="number" min="2" max="60" step="1" id="heroAdminInterval"></div>
            <div class="form-group"><label>ارتفاع الـHero (بالبكسل)</label><input type="number" min="420" max="760" step="10" id="heroAdminHeight"></div>
            <div class="form-group wide"><label>نص تلميح التمرير</label><input type="text" maxlength="80" id="heroAdminScrollLabel"></div>
          </div>
          <div id="heroSlidesList"></div>
          <button class="add-btn" id="addHeroSlideBtn" type="button">➕ إضافة شريحة جديدة</button>
        </div>
        <button class="btn-primary save-settings" id="saveHeroBtn" type="button">حفظ إعدادات الـHero والشرائح</button>
      </div>

      <!-- قسم الطلبات -->
      <div class="panel" id="panel-orders">'''
if panel_marker not in admin:
    raise SystemExit('orders panel marker not found')
admin = admin.replace(panel_marker, hero_panel, 1)

# Replace old Hero editor in feature settings with a pointer to the independent tab.
old_feature_hero = '''          <div class="control-section">
            <h3 class="control-section-title">الواجهة الرئيسية والـHero</h3>
            <div class="admin-note">يتحكم هذا القسم في الـHero الجديد الذي يحل محل الواجهة القديمة. اترك الميزات الجديدة متوقفة في البداية، ثم فعّلها واحدةً تلو الأخرى لمراجعة شكلها في المتجر.</div>
            <div class="hero-settings-grid">
              <div class="feature-control"><div><h3>إظهار الـHero</h3><p>إخفاؤه يزيل الـHero الجديد بالكامل من الصفحة الرئيسية.</p><span class="feature-state" data-state-for="heroVisible">—</span></div><label class="switch" aria-label="إظهار الـHero"><input type="checkbox" id="heroVisible" checked><span></span></label></div>
              <div class="feature-control"><div><h3>إظهار شريط المسارات</h3><p>يُظهر أو يخفي بطاقات المسارات أسفل الـHero بحسب الميزات المفعّلة.</p><span class="feature-state" data-state-for="heroFeatureRailVisible">—</span></div><label class="switch" aria-label="إظهار شريط مسارات الـHero"><input type="checkbox" id="heroFeatureRailVisible" checked><span></span></label></div>
            </div>
            <div class="hero-copy-grid">
              <div class="form-group"><label for="heroTitleInput">عنوان الـHero</label><input id="heroTitleInput" maxlength="120" value="كتابك القادم يبدأ من هنا"></div>
              <div class="form-group"><label for="heroSubtitleInput">النص التوضيحي</label><textarea id="heroSubtitleInput" rows="3" maxlength="240">كتب وروايات اخترناها بعناية؛ لأن الكتاب المناسب لا يملأ وقتك فقط، بل يترك فيك أثرًا.</textarea></div>
              <div class="form-group"><label for="heroPrimaryLabelInput">نص الزر الأساسي</label><input id="heroPrimaryLabelInput" maxlength="60" value="اكتشف كتابك القادم"></div>
              <div class="form-group"><label for="heroSecondaryLabelInput">نص الزر الثانوي</label><input id="heroSecondaryLabelInput" maxlength="60" value="اختر هدية تحمل معنى"></div>
            </div>
            <div class="hero-cta-grid">
              <div class="feature-control"><div><h3>إظهار الزر الأساسي</h3><p>يرتبط بميزة اكتشاف كتابك.</p><span class="feature-state" data-state-for="heroPrimaryVisible">—</span></div><label class="switch" aria-label="إظهار الزر الأساسي"><input type="checkbox" id="heroPrimaryVisible" checked><span></span></label></div>
              <div class="feature-control"><div><h3>إظهار الزر الثانوي</h3><p>يرتبط بمسار الهدايا.</p><span class="feature-state" data-state-for="heroSecondaryVisible">—</span></div><label class="switch" aria-label="إظهار الزر الثانوي"><input type="checkbox" id="heroSecondaryVisible" checked><span></span></label></div>
            </div>
          </div>'''
new_feature_hero = '''          <div class="control-section">
            <h3 class="control-section-title">الواجهة الرئيسية والـHero</h3>
            <div class="admin-note">أصبحت كل تفاصيل الـHero في تبويب مستقل باسم «إدارة الـHero» بجانب إدارة الكتب. انتقل إليه لإضافة الشرائح وترتيبها وتعديل الأزرار والصور وإعدادات التبديل.</div>
          </div>'''
if old_feature_hero not in admin:
    raise SystemExit('old feature hero editor not found')
admin = admin.replace(old_feature_hero, new_feature_hero, 1)

# State: retain full settings when saving either panel.
marker = '''    const ADMIN_EMAIL = 'baakbook01@gmail.com';
    const firebaseApp = initializeApp(window.BAAK_RUNTIME.FIREBASE);'''
replacement = '''    const ADMIN_EMAIL = 'baakbook01@gmail.com';
    let settingsState = { features: {}, storefront: {} };
    let heroAdminConfig = null;
    const firebaseApp = initializeApp(window.BAAK_RUNTIME.FIREBASE);'''
if marker not in admin:
    raise SystemExit('admin state marker not found')
admin = admin.replace(marker, replacement, 1)

# Tab routing.
old_tab_route = '''        else if (target === 'features') loadSettings();'''
new_tab_route = '''        else if (target === 'features') loadSettings();
        else if (target === 'hero') loadHeroEditor();'''
if old_tab_route not in admin:
    raise SystemExit('tab route marker not found')
admin = admin.replace(old_tab_route, new_tab_route, 1)

# loadAllData loadHeroEditor is called after settings.
old_load_all = '''      await loadDeliveryFees();
      await loadSettings();
    }'''
new_load_all = '''      await loadDeliveryFees();
      await loadSettings();
      loadHeroEditor();
    }'''
if old_load_all not in admin:
    raise SystemExit('loadAllData marker not found')
admin = admin.replace(old_load_all, new_load_all, 1)

old_settings_block = '''    async function loadSettings() {
      try {
        const res = await adminFetch(`${API_BASE}/admin/settings`, { headers: apiHeaders() });
        if (!res.ok) throw new Error('تعذر تحميل إعدادات ميزات المتجر');
        const data = await res.json();
        Object.entries(featureMap).forEach(([key, id]) => {
          if ($(id)) $(id).checked = Boolean(data.features && data.features[key]);
        });
        const hero = { ...heroDefaults, ...(data.storefront?.hero || {}) };
        $('heroVisible').checked = hero.visible !== false;
        $('heroFeatureRailVisible').checked = hero.feature_rail_visible !== false;
        $('heroPrimaryVisible').checked = hero.primary_cta_visible !== false;
        $('heroSecondaryVisible').checked = hero.secondary_cta_visible !== false;
        $('heroTitleInput').value = hero.title;
        $('heroSubtitleInput').value = hero.subtitle;
        $('heroPrimaryLabelInput').value = hero.primary_cta_label;
        $('heroSecondaryLabelInput').value = hero.secondary_cta_label;
        updateFeatureStates();
      } catch (err) {
        toast(err.message, 'error');
      }
    }'''
new_settings_block = '''    async function loadSettings() {
      try {
        const res = await adminFetch(`${API_BASE}/admin/settings`, { headers: apiHeaders() });
        if (!res.ok) throw new Error('تعذر تحميل إعدادات المتجر');
        const data = await res.json();
        settingsState = { features: { ...(data.features || {}) }, storefront: { ...(data.storefront || {}) } };
        Object.entries(featureMap).forEach(([key, id]) => { if ($(id)) $(id).checked = Boolean(settingsState.features[key]); });
        heroAdminConfig = normalizeHeroAdmin(settingsState.storefront.hero || {});
        updateFeatureStates();
        if ($('panel-hero')?.classList.contains('active')) renderHeroEditor();
      } catch (err) { toast(err.message, 'error'); }
    }'''
if old_settings_block not in admin:
    raise SystemExit('old admin settings block not found')
admin = admin.replace(old_settings_block, new_settings_block, 1)

old_save_settings = '''    $('saveSettingsBtn').onclick = async () => {
      const features = {};
      Object.entries(featureMap).forEach(([key, id]) => { features[key] = Boolean($(id)?.checked); });
      const storefront = { hero: {
        visible: Boolean($('heroVisible')?.checked),
        feature_rail_visible: Boolean($('heroFeatureRailVisible')?.checked),
        primary_cta_visible: Boolean($('heroPrimaryVisible')?.checked),
        secondary_cta_visible: Boolean($('heroSecondaryVisible')?.checked),
        title: $('heroTitleInput')?.value.trim() || 'كتابك القادم يبدأ من هنا',
        subtitle: $('heroSubtitleInput')?.value.trim() || 'كتب وروايات اخترناها بعناية؛ لأن الكتاب المناسب لا يملأ وقتك فقط، بل يترك فيك أثرًا.',
        primary_cta_label: $('heroPrimaryLabelInput')?.value.trim() || 'اكتشف كتابك القادم',
        secondary_cta_label: $('heroSecondaryLabelInput')?.value.trim() || 'اختر هدية تحمل معنى'
      } };
      try {
        updateFeatureStates();
        const res = await adminFetch(`${API_BASE}/admin/settings`, {
          method: 'PUT', headers: apiHeaders(), body: JSON.stringify({ features, storefront })
        });
        if (!res.ok) throw new Error('تعذر حفظ تغييرات ميزات المتجر');
        toast('تم حفظ تغييرات ميزات المتجر', 'success');
      } catch (err) {
        toast(err.message, 'error');
      }
    };'''
new_save_settings = '''    $('saveSettingsBtn').onclick = async () => {
      const features = {};
      Object.entries(featureMap).forEach(([key, id]) => { features[key] = Boolean($(id)?.checked); });
      const storefront = { ...settingsState.storefront, hero: heroAdminConfig || normalizeHeroAdmin(settingsState.storefront.hero || {}) };
      try {
        updateFeatureStates();
        const res = await adminFetch(`${API_BASE}/admin/settings`, { method: 'PUT', headers: apiHeaders(), body: JSON.stringify({ features, storefront }) });
        if (!res.ok) throw new Error('تعذر حفظ تغييرات ميزات المتجر');
        settingsState = { features, storefront };
        toast('تم حفظ تغييرات ميزات المتجر', 'success');
      } catch (err) { toast(err.message, 'error'); }
    };'''
if old_save_settings not in admin:
    raise SystemExit('old admin save settings block not found')
admin = admin.replace(old_save_settings, new_save_settings, 1)

# Insert Hero editor before delivery fees section.
hero_js_marker = '''    // ========== DELIVERY FEES =========='''
hero_js = r'''    // ========== HERO MANAGEMENT ==========
    const DEFAULT_HERO_ADMIN = {
      visible: true, autoplay: true, interval: 6, dots: true, arrows: true, scroll_hint: true,
      scroll_hint_label: 'مرّر لاكتشاف الكتب', height: 540, pause_on_interaction: true, feature_rail_visible: true,
      slides: [{ id: `hero-${Date.now()}`, active: true, image: 'https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?auto=format&fit=crop&w=1800&q=85', image_alt: 'كتب مفتوحة على طاولة', eyebrow: 'Baak Books', eyebrow_en: '', title: 'كتابك القادم يبدأ من هنا', title_en: '', text: 'كتب وروايات اخترناها بعناية؛ لأن الكتاب المناسب لا يملأ وقتك فقط، بل يترك فيك أثرًا.', text_en: '', primary_visible: true, primary_label: 'اكتشف كتابك القادم', primary_label_en: '', primary_action: 'discovery', primary_link: '', secondary_visible: true, secondary_label: 'اختر هدية تحمل معنى', secondary_label_en: '', secondary_action: 'gift', secondary_link: '', reflection: true, text_backdrop: true, text_color_mode: 'manual', text_color: '#ffffff', auto_text_color: '#ffffff' }]
    };
    function normalizeHeroAdmin(raw = {}) {
      const result = { ...DEFAULT_HERO_ADMIN, ...raw };
      result.slides = Array.isArray(raw.slides) && raw.slides.length ? raw.slides.map(slide => ({ ...DEFAULT_HERO_ADMIN.slides[0], ...slide })) : DEFAULT_HERO_ADMIN.slides.map(slide => ({ ...slide, id: `hero-${Date.now()}` }));
      return result;
    }
    function adminEsc(value) { return String(value ?? '').replace(/[&<>"']/g, char => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#039;' }[char])); }
    function heroActionOptions(selected) {
      return [['discovery','打开「发现书单」'],['gift','打开「送礼」'],['on_demand','عرض كتب يمكن اقتناؤها'],['ideas_lab','فتح مختبر الأفكار'],['link','رابط مخصص']].map(([value,label]) => `<option value="${value}" ${selected === value ? 'selected' : ''}>${label}</option>`).join('');
    }
    function heroSlideRow(slide, index, total) {
      return `<div class="hero-slide-card" data-hero-id="${adminEsc(slide.id)}">
        <div class="hero-slide-head"><h3>الشريحة ${index + 1}</h3><div class="hero-slide-order"><button type="button" class="hero-up" ${index === 0 ? 'disabled' : ''}>↑ أعلى</button><button type="button" class="hero-down" ${index === total - 1 ? 'disabled' : ''}>↓ أسفل</button></div></div>
        <div class="hero-slide-form">
          <label class="hero-check"><input type="checkbox" class="s-active" ${slide.active !== false ? 'checked' : ''}> الشريحة مفعّلة</label>
          <div class="form-group"><label>الشارة الصغيرة فوق العنوان</label><input class="s-eyebrow" maxlength="80" value="${adminEsc(slide.eyebrow)}"></div>
          <div class="form-group"><label>Eyebrow (EN — اختياري)</label><input class="s-eyebrow-en" maxlength="80" value="${adminEsc(slide.eyebrow_en)}"></div>
          <div class="form-group wide"><label>العنوان الرئيسي</label><input class="s-title" maxlength="140" value="${adminEsc(slide.title)}"></div>
          <div class="form-group"><label>Title (EN — اختياري)</label><input class="s-title-en" maxlength="140" value="${adminEsc(slide.title_en)}"></div>
          <div class="form-group wide"><label>الوصف</label><textarea class="s-text" maxlength="360">${adminEsc(slide.text)}</textarea></div>
          <div class="form-group"><label>Description (EN — اختياري)</label><textarea class="s-text-en" maxlength="360">${adminEsc(slide.text_en)}</textarea></div>
          <div class="form-group wide"><label>صورة الخلفية (URL)</label><input class="s-image" type="url" maxlength="700" value="${adminEsc(slide.image)}" placeholder="https://..."><img class="hero-slide-preview" src="${adminEsc(slide.image)}" alt="معاينة الصورة" onerror="this.style.display='none'" onload="this.style.display='block'"></div>
          <div class="form-group wide"><label>النص البديل للصورة</label><input class="s-alt" maxlength="180" value="${adminEsc(slide.image_alt)}"></div>
          <label class="hero-check"><input type="checkbox" class="s-primary-visible" ${slide.primary_visible !== false ? 'checked' : ''}> إظهار الزر الأساسي</label>
          <div class="form-group"><label>نص الزر الأساسي</label><input class="s-primary-label" maxlength="70" value="${adminEsc(slide.primary_label)}"></div>
          <div class="form-group"><label>وجهة الزر الأساسي</label><select class="s-primary-action">${heroActionOptions(slide.primary_action || 'discovery')}</select></div>
          <div class="form-group"><label>الرابط الأساسي عند اختيار «رابط مخصص»</label><input class="s-primary-link" type="url" maxlength="700" value="${adminEsc(slide.primary_link)}" placeholder="https://... أو #books"></div>
          <label class="hero-check"><input type="checkbox" class="s-secondary-visible" ${slide.secondary_visible !== false ? 'checked' : ''}> إظهار الزر الثانوي</label>
          <div class="form-group"><label>نص الزر الثانوي</label><input class="s-secondary-label" maxlength="70" value="${adminEsc(slide.secondary_label)}"></div>
          <div class="form-group"><label>وجهة الزر الثانوي</label><select class="s-secondary-action">${heroActionOptions(slide.secondary_action || 'gift')}</select></div>
          <div class="form-group"><label>الرابط الثانوي عند اختيار «رابط مخصص»</label><input class="s-secondary-link" type="url" maxlength="700" value="${adminEsc(slide.secondary_link)}" placeholder="https://... أو #books"></div>
          <label class="hero-check"><input type="checkbox" class="s-reflection" ${slide.reflection ? 'checked' : ''}> تظليل علوي خفيف لتحسين وضوح الشعار والقائمة</label>
          <label class="hero-check"><input type="checkbox" class="s-text-backdrop" ${slide.text_backdrop ? 'checked' : ''}> ظل ناعم خلف نص الشريحة</label>
          <div class="form-group"><label>لون النص</label><select class="s-text-color-mode"><option value="auto" ${slide.text_color_mode !== 'manual' ? 'selected' : ''}>تلقائي</option><option value="manual" ${slide.text_color_mode === 'manual' ? 'selected' : ''}>يدوي</option></select></div>
          <div class="form-group"><label>اللون اليدوي</label><input class="s-text-color" type="color" value="${adminEsc(slide.text_color || '#ffffff')}"></div>
        </div>
        <button type="button" class="btn-secondary danger-outline hero-remove">حذف الشريحة</button>
      </div>`;
    }
    function renderHeroEditor() {
      if (!heroAdminConfig) heroAdminConfig = normalizeHeroAdmin();
      $('heroAdminVisible').checked = heroAdminConfig.visible !== false; $('heroAdminAutoplay').checked = heroAdminConfig.autoplay !== false; $('heroAdminDots').checked = heroAdminConfig.dots !== false; $('heroAdminArrows').checked = heroAdminConfig.arrows !== false; $('heroAdminScrollHint').checked = heroAdminConfig.scroll_hint !== false; $('heroAdminPause').checked = heroAdminConfig.pause_on_interaction !== false; $('heroAdminInterval').value = heroAdminConfig.interval || 6; $('heroAdminHeight').value = heroAdminConfig.height || 540; $('heroAdminScrollLabel').value = heroAdminConfig.scroll_hint_label || 'مرّر لاكتشاف الكتب';
      $('heroSlidesList').innerHTML = heroAdminConfig.slides.length ? heroAdminConfig.slides.map((slide, index) => heroSlideRow(slide, index, heroAdminConfig.slides.length)).join('') : '<div class="hero-empty">لا توجد شرائح. أضف شريحة جديدة للبدء.</div>';
      document.querySelectorAll('.hero-slide-card').forEach(card => {
        const id = card.dataset.heroId; const index = heroAdminConfig.slides.findIndex(slide => slide.id === id);
        card.querySelector('.hero-up')?.addEventListener('click', () => { if (index > 0) { [heroAdminConfig.slides[index - 1], heroAdminConfig.slides[index]] = [heroAdminConfig.slides[index], heroAdminConfig.slides[index - 1]]; renderHeroEditor(); } });
        card.querySelector('.hero-down')?.addEventListener('click', () => { if (index < heroAdminConfig.slides.length - 1) { [heroAdminConfig.slides[index + 1], heroAdminConfig.slides[index]] = [heroAdminConfig.slides[index], heroAdminConfig.slides[index + 1]]; renderHeroEditor(); } });
        card.querySelector('.hero-remove')?.addEventListener('click', () => { heroAdminConfig.slides = heroAdminConfig.slides.filter(slide => slide.id !== id); renderHeroEditor(); });
        card.querySelector('.s-image')?.addEventListener('input', event => { const preview = card.querySelector('.hero-slide-preview'); preview.src = event.target.value.trim(); preview.style.display = event.target.value.trim() ? 'block' : 'none'; });
      });
    }
    function loadHeroEditor() { if (!heroAdminConfig) heroAdminConfig = normalizeHeroAdmin(); renderHeroEditor(); }
    function collectHeroEditor() {
      const slides = [];
      document.querySelectorAll('.hero-slide-card').forEach(card => {
        const old = heroAdminConfig.slides.find(slide => slide.id === card.dataset.heroId) || {};
        slides.push({ ...old, id: card.dataset.heroId, active: card.querySelector('.s-active').checked, eyebrow: card.querySelector('.s-eyebrow').value.trim(), eyebrow_en: card.querySelector('.s-eyebrow-en').value.trim(), title: card.querySelector('.s-title').value.trim(), title_en: card.querySelector('.s-title-en').value.trim(), text: card.querySelector('.s-text').value.trim(), text_en: card.querySelector('.s-text-en').value.trim(), image: card.querySelector('.s-image').value.trim(), image_alt: card.querySelector('.s-alt').value.trim(), primary_visible: card.querySelector('.s-primary-visible').checked, primary_label: card.querySelector('.s-primary-label').value.trim(), primary_action: card.querySelector('.s-primary-action').value, primary_link: card.querySelector('.s-primary-link').value.trim(), secondary_visible: card.querySelector('.s-secondary-visible').checked, secondary_label: card.querySelector('.s-secondary-label').value.trim(), secondary_action: card.querySelector('.s-secondary-action').value, secondary_link: card.querySelector('.s-secondary-link').value.trim(), reflection: card.querySelector('.s-reflection').checked, text_backdrop: card.querySelector('.s-text-backdrop').checked, text_color_mode: card.querySelector('.s-text-color-mode').value, text_color: card.querySelector('.s-text-color').value });
      });
      return { ...heroAdminConfig, visible: $('heroAdminVisible').checked, autoplay: $('heroAdminAutoplay').checked, dots: $('heroAdminDots').checked, arrows: $('heroAdminArrows').checked, scroll_hint: $('heroAdminScrollHint').checked, pause_on_interaction: $('heroAdminPause').checked, interval: Math.max(2, Math.min(60, Number($('heroAdminInterval').value) || 6)), height: Math.max(420, Math.min(760, Number($('heroAdminHeight').value) || 540)), scroll_hint_label: $('heroAdminScrollLabel').value.trim() || 'مرّر لاكتشاف الكتب', slides };
    }
    $('addHeroSlideBtn').onclick = () => { heroAdminConfig = heroAdminConfig || normalizeHeroAdmin(); heroAdminConfig.slides.push({ ...DEFAULT_HERO_ADMIN.slides[0], id: `hero-${Date.now()}-${heroAdminConfig.slides.length}`, active: true, title: 'عنوان شريحة جديد', text: 'اكتب وصفًا واضحًا يعرّف القارئ بما ينتظره هنا.', image: '' }); renderHeroEditor(); };
    $('saveHeroBtn').onclick = async () => { try { const hero = collectHeroEditor(); const features = settingsState.features || {}; const storefront = { ...(settingsState.storefront || {}), hero }; const res = await adminFetch(`${API_BASE}/admin/settings`, { method: 'PUT', headers: apiHeaders(), body: JSON.stringify({ features, storefront }) }); if (!res.ok) throw new Error('تعذر حفظ إعدادات الـHero'); heroAdminConfig = hero; settingsState = { features, storefront }; toast('تم حفظ إعدادات الـHero والشرائح', 'success'); } catch (error) { toast(error.message, 'error'); } };

'''
if hero_js_marker not in admin:
    raise SystemExit('hero JS insertion marker not found')
admin = admin.replace(hero_js_marker, hero_js + hero_js_marker, 1)

ADMIN.write_text(admin)
print('UPDATED index.html and admin.html')
