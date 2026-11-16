import os

def create_svgs():
    images_dir = os.path.join('static', 'images')
    os.makedirs(images_dir, exist_ok=True)

    svgs = {
        'acetone.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_ace" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <linearGradient id="liq_ace" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#0891b2" stop-opacity="0.95"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_ace)"/>
  <circle cx="200" cy="200" r="140" fill="#0284c7" opacity="0.08"/>
  <rect x="170" y="80" width="60" height="35" rx="4" fill="#475569" stroke="#94a3b8" stroke-width="2"/>
  <rect x="160" y="115" width="80" height="20" rx="3" fill="#334155" stroke="#64748b" stroke-width="2"/>
  <path d="M160 135 L120 190 L120 310 Q120 325 135 325 L265 325 Q280 325 280 310 L280 190 L240 135 Z" fill="url(#liq_ace)" stroke="#38bdf8" stroke-width="3"/>
  <path d="M125 210 Q200 220 275 210 L275 310 Q275 320 265 320 L135 320 Q125 320 125 310 Z" fill="#0284c7" opacity="0.7"/>
  <circle cx="160" cy="260" r="8" fill="#ffffff" opacity="0.4"/>
  <circle cx="230" cy="240" r="6" fill="#ffffff" opacity="0.35"/>
  <circle cx="190" cy="280" r="10" fill="#ffffff" opacity="0.3"/>
  <rect x="145" y="220" width="110" height="70" rx="6" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
  <text x="200" y="242" font-family="sans-serif" font-size="14" font-weight="800" fill="#0f172a" text-anchor="middle">ACETONE</text>
  <text x="200" y="258" font-family="sans-serif" font-size="10" font-weight="600" fill="#dc2626" text-anchor="middle">99.5% TECH</text>
  <text x="200" y="274" font-family="sans-serif" font-size="9" fill="#475569" text-anchor="middle">CH3COCH3</text>
</svg>''',

        'ethanol.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_eth" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <linearGradient id="amber_bottle" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#b45309"/>
      <stop offset="100%" stop-color="#78350f"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_eth)"/>
  <circle cx="200" cy="200" r="140" fill="#f59e0b" opacity="0.08"/>
  <rect x="175" y="75" width="50" height="30" rx="4" fill="#1e293b" stroke="#f59e0b" stroke-width="2"/>
  <path d="M175 105 L150 145 L150 320 Q150 330 160 330 L240 330 Q250 330 250 320 L250 145 L225 105 Z" fill="url(#amber_bottle)" stroke="#fbbf24" stroke-width="2"/>
  <rect x="165" y="190" width="70" height="95" rx="4" fill="#ffffff" stroke="#d97706" stroke-width="2"/>
  <text x="200" y="215" font-family="sans-serif" font-size="12" font-weight="800" fill="#991b1b" text-anchor="middle">ETHANOL</text>
  <text x="200" y="230" font-family="sans-serif" font-size="10" font-weight="700" fill="#1e293b" text-anchor="middle">99% ACS</text>
  <text x="200" y="246" font-family="sans-serif" font-size="9" fill="#475569" text-anchor="middle">C2H5OH</text>
  <rect x="180" y="255" width="40" height="14" fill="#ef4444" rx="2"/>
  <text x="200" y="265" font-family="sans-serif" font-size="8" font-weight="bold" fill="#fff" text-anchor="middle">FLAMMABLE</text>
</svg>''',

        'isopropyl.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_iso" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_iso)"/>
  <circle cx="200" cy="200" r="140" fill="#10b981" opacity="0.08"/>
  <rect x="130" y="120" width="140" height="195" rx="16" fill="#e2e8f0" stroke="#38bdf8" stroke-width="3"/>
  <path d="M150 120 L150 85 L210 85 L210 120" fill="none" stroke="#cbd5e1" stroke-width="12" stroke-linecap="round"/>
  <rect x="215" y="75" width="40" height="30" rx="4" fill="#ef4444" stroke="#b91c1c" stroke-width="2"/>
  <rect x="145" y="170" width="110" height="105" rx="6" fill="#1e293b" stroke="#10b981" stroke-width="2"/>
  <text x="200" y="198" font-family="sans-serif" font-size="14" font-weight="800" fill="#10b981" text-anchor="middle">ISOPROPYL</text>
  <text x="200" y="216" font-family="sans-serif" font-size="12" font-weight="700" fill="#f8fafc" text-anchor="middle">ALCOHOL</text>
  <text x="200" y="234" font-family="sans-serif" font-size="10" font-weight="bold" fill="#38bdf8" text-anchor="middle">99.9% PURE</text>
  <text x="200" y="252" font-family="sans-serif" font-size="9" fill="#94a3b8" text-anchor="middle">USP Grade</text>
</svg>''',

        'hydrochloric.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_hcl" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_hcl)"/>
  <circle cx="200" cy="200" r="140" fill="#eab308" opacity="0.08"/>
  <rect x="180" y="80" width="40" height="35" rx="3" fill="#f59e0b" stroke="#d97706" stroke-width="2"/>
  <path d="M175 115 L145 160 L145 320 Q145 330 155 330 L245 330 Q255 330 255 320 L255 160 L225 115 Z" fill="#334155" stroke="#f59e0b" stroke-width="2.5"/>
  <rect x="160" y="190" width="80" height="105" rx="4" fill="#ffffff" stroke="#334155" stroke-width="1.5"/>
  <text x="200" y="212" font-family="sans-serif" font-size="11" font-weight="800" fill="#0f172a" text-anchor="middle">HYDROCHLORIC</text>
  <text x="200" y="226" font-family="sans-serif" font-size="10" font-weight="700" fill="#dc2626" text-anchor="middle">ACID 37%</text>
  <text x="200" y="240" font-family="sans-serif" font-size="9" fill="#475569" text-anchor="middle">Reagent Grade</text>
  <polygon points="200,248 215,263 200,278 185,263" fill="#fff" stroke="#dc2626" stroke-width="2"/>
  <text x="200" y="267" font-family="sans-serif" font-size="11" font-weight="bold" fill="#dc2626" text-anchor="middle">COR</text>
</svg>''',

        'sulfuric.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_suf" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_suf)"/>
  <circle cx="200" cy="200" r="140" fill="#ef4444" opacity="0.08"/>
  <rect x="175" y="75" width="50" height="35" rx="4" fill="#dc2626" stroke="#b91c1c" stroke-width="2"/>
  <path d="M175 110 L145 150 L145 320 Q145 330 155 330 L245 330 Q255 330 255 320 L255 150 L225 110 Z" fill="#1e293b" stroke="#ef4444" stroke-width="3"/>
  <rect x="160" y="185" width="80" height="110" rx="4" fill="#ffffff" stroke="#ef4444" stroke-width="2"/>
  <text x="200" y="208" font-family="sans-serif" font-size="12" font-weight="800" fill="#b91c1c" text-anchor="middle">SULFURIC</text>
  <text x="200" y="224" font-family="sans-serif" font-size="11" font-weight="700" fill="#0f172a" text-anchor="middle">ACID 98%</text>
  <text x="200" y="240" font-family="sans-serif" font-size="10" fill="#475569" text-anchor="middle">H2SO4</text>
  <rect x="175" y="250" width="50" height="16" fill="#ef4444" rx="2"/>
  <text x="200" y="262" font-family="sans-serif" font-size="8" font-weight="bold" fill="#fff" text-anchor="middle">DANGER</text>
</svg>''',

        'sodium_hydroxide.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_naoh" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_naoh)"/>
  <circle cx="200" cy="200" r="140" fill="#3b82f6" opacity="0.08"/>
  <rect x="140" y="110" width="120" height="210" rx="14" fill="#f8fafc" stroke="#3b82f6" stroke-width="3"/>
  <rect x="165" y="80" width="70" height="30" rx="4" fill="#2563eb"/>
  <rect x="155" y="160" width="90" height="120" rx="4" fill="#1e293b" stroke="#60a5fa" stroke-width="2"/>
  <text x="200" y="185" font-family="sans-serif" font-size="11" font-weight="800" fill="#60a5fa" text-anchor="middle">SODIUM</text>
  <text x="200" y="200" font-family="sans-serif" font-size="11" font-weight="800" fill="#f8fafc" text-anchor="middle">HYDROXIDE</text>
  <text x="200" y="220" font-family="sans-serif" font-size="9" fill="#94a3b8" text-anchor="middle">99% PURE PELLETS</text>
  <text x="200" y="240" font-family="sans-serif" font-size="10" font-weight="bold" fill="#f59e0b" text-anchor="middle">NaOH &middot; 1 KG</text>
</svg>''',

        'beakers.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_glass" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_glass)"/>
  <circle cx="200" cy="200" r="140" fill="#38bdf8" opacity="0.08"/>
  <path d="M120 120 L135 120 L135 300 Q135 315 150 315 L250 315 Q265 315 265 300 L265 120 L275 120" fill="none" stroke="#38bdf8" stroke-width="4" stroke-linecap="round"/>
  <path d="M120 120 L110 115" stroke="#38bdf8" stroke-width="4" stroke-linecap="round"/>
  <path d="M139 210 Q200 215 261 210 L261 300 Q261 311 250 311 L150 311 Q139 311 139 300 Z" fill="#0284c7" opacity="0.75"/>
  <line x1="230" y1="160" x2="255" y2="160" stroke="#94a3b8" stroke-width="2"/>
  <line x1="235" y1="190" x2="255" y2="190" stroke="#94a3b8" stroke-width="2"/>
  <line x1="230" y1="220" x2="255" y2="220" stroke="#ffffff" stroke-width="2"/>
  <line x1="235" y1="250" x2="255" y2="250" stroke="#ffffff" stroke-width="2"/>
  <text x="220" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8" text-anchor="end">800ml</text>
  <text x="220" y="224" font-family="sans-serif" font-size="10" fill="#ffffff" text-anchor="end">400ml</text>
  <path d="M270 200 L280 200 L280 310 Q280 315 285 315 L335 315 Q340 315 340 310 L340 200" fill="none" stroke="#a855f7" stroke-width="3"/>
  <path d="M282 250 L338 250 L338 310 L282 310 Z" fill="#9333ea" opacity="0.6"/>
  <text x="200" y="360" font-family="sans-serif" font-size="14" font-weight="700" fill="#38bdf8" text-anchor="middle">BOROSILICATE 3.3 SET</text>
</svg>''',

        'erlenmeyer.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_erl" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_erl)"/>
  <circle cx="200" cy="200" r="140" fill="#a855f7" opacity="0.08"/>
  <path d="M185 80 L215 80 L215 130 L285 290 Q290 305 275 305 L125 305 Q110 305 115 290 L185 130 Z" fill="none" stroke="#a855f7" stroke-width="4"/>
  <path d="M140 240 L260 240 L275 295 Q280 302 270 302 L130 302 Q120 302 125 295 Z" fill="#7c3aed" opacity="0.7"/>
  <circle cx="180" cy="270" r="6" fill="#fff" opacity="0.5"/>
  <circle cx="220" cy="260" r="8" fill="#fff" opacity="0.4"/>
  <text x="200" y="355" font-family="sans-serif" font-size="14" font-weight="700" fill="#a855f7" text-anchor="middle">ERLENMEYER FLASK 1000mL</text>
</svg>''',

        'condenser.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_cnd" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_cnd)"/>
  <circle cx="200" cy="200" r="140" fill="#06b6d4" opacity="0.08"/>
  <rect x="175" y="70" width="50" height="230" rx="10" fill="none" stroke="#38bdf8" stroke-width="3"/>
  <line x1="200" y1="50" x2="200" y2="320" stroke="#0284c7" stroke-width="5"/>
  <line x1="175" y1="120" x2="135" y2="110" stroke="#38bdf8" stroke-width="4" stroke-linecap="round"/>
  <line x1="225" y1="250" x2="265" y2="240" stroke="#38bdf8" stroke-width="4" stroke-linecap="round"/>
  <text x="200" y="360" font-family="sans-serif" font-size="14" font-weight="700" fill="#38bdf8" text-anchor="middle">LIEBIG CONDENSER 300mm</text>
</svg>''',

        'scale.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_scale" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_scale)"/>
  <circle cx="200" cy="200" r="140" fill="#10b981" opacity="0.08"/>
  <rect x="90" y="180" width="220" height="120" rx="14" fill="#334155" stroke="#64748b" stroke-width="3"/>
  <ellipse cx="200" cy="150" rx="80" ry="22" fill="#94a3b8" stroke="#cbd5e1" stroke-width="3"/>
  <rect x="190" y="155" width="20" height="30" fill="#64748b"/>
  <rect x="130" y="210" width="140" height="45" rx="6" fill="#022c22" stroke="#10b981" stroke-width="2"/>
  <text x="200" y="240" font-family="monospace" font-size="24" font-weight="800" fill="#34d399" text-anchor="middle">125.042 g</text>
  <circle cx="145" cy="275" r="10" fill="#475569" stroke="#94a3b8" stroke-width="1.5"/>
  <text x="145" y="278" font-family="sans-serif" font-size="8" font-weight="bold" fill="#fff" text-anchor="middle">TARE</text>
  <circle cx="185" cy="275" r="10" fill="#475569" stroke="#94a3b8" stroke-width="1.5"/>
  <text x="185" y="278" font-family="sans-serif" font-size="8" font-weight="bold" fill="#fff" text-anchor="middle">CAL</text>
  <circle cx="225" cy="275" r="10" fill="#475569" stroke="#94a3b8" stroke-width="1.5"/>
  <text x="225" y="278" font-family="sans-serif" font-size="8" font-weight="bold" fill="#fff" text-anchor="middle">UNIT</text>
  <circle cx="260" cy="275" r="10" fill="#ef4444" stroke="#b91c1c" stroke-width="1.5"/>
  <text x="260" y="278" font-family="sans-serif" font-size="8" font-weight="bold" fill="#fff" text-anchor="middle">ON</text>
  <text x="200" y="350" font-family="sans-serif" font-size="14" font-weight="700" fill="#10b981" text-anchor="middle">0.001g PRECISION BALANCE</text>
</svg>''',

        'vintage_scale.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_vnt" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_vnt)"/>
  <circle cx="200" cy="200" r="140" fill="#f59e0b" opacity="0.08"/>
  <rect x="130" y="300" width="140" height="25" rx="4" fill="#78350f" stroke="#d97706" stroke-width="2"/>
  <line x1="200" y1="300" x2="200" y2="110" stroke="#f59e0b" stroke-width="8"/>
  <line x1="120" y1="120" x2="280" y2="120" stroke="#f59e0b" stroke-width="6" stroke-linecap="round"/>
  <line x1="130" y1="120" x2="110" y2="200" stroke="#d97706" stroke-width="2"/>
  <line x1="130" y1="120" x2="150" y2="200" stroke="#d97706" stroke-width="2"/>
  <path d="M100 200 Q130 220 160 200 Z" fill="#fbbf24" stroke="#d97706" stroke-width="2"/>
  <line x1="270" y1="120" x2="250" y2="200" stroke="#d97706" stroke-width="2"/>
  <line x1="270" y1="120" x2="290" y2="200" stroke="#d97706" stroke-width="2"/>
  <path d="M240 200 Q270 220 300 200 Z" fill="#fbbf24" stroke="#d97706" stroke-width="2"/>
  <text x="200" y="360" font-family="sans-serif" font-size="14" font-weight="700" fill="#f59e0b" text-anchor="middle">ANTIQUE BRASS LAB BALANCE</text>
</svg>''',

        'ph_meter.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_ph" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_ph)"/>
  <circle cx="200" cy="200" r="140" fill="#06b6d4" opacity="0.08"/>
  <rect x="160" y="70" width="80" height="180" rx="16" fill="#0284c7" stroke="#38bdf8" stroke-width="3"/>
  <rect x="175" y="95" width="50" height="40" rx="4" fill="#082f49" stroke="#38bdf8" stroke-width="1.5"/>
  <text x="200" y="122" font-family="monospace" font-size="18" font-weight="bold" fill="#38bdf8" text-anchor="middle">7.02</text>
  <circle cx="200" cy="160" r="12" fill="#f59e0b"/>
  <circle cx="200" cy="195" r="10" fill="#e2e8f0"/>
  <circle cx="200" cy="225" r="8" fill="#94a3b8"/>
  <rect x="190" y="250" width="20" height="80" rx="2" fill="#cbd5e1" stroke="#94a3b8" stroke-width="1.5"/>
  <circle cx="200" cy="330" r="12" fill="#38bdf8" opacity="0.7" stroke="#0284c7" stroke-width="2"/>
  <text x="200" y="370" font-family="sans-serif" font-size="14" font-weight="700" fill="#38bdf8" text-anchor="middle">DIGITAL pH TESTER PRO</text>
</svg>''',

        'gloves.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_glv" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_glv)"/>
  <circle cx="200" cy="200" r="140" fill="#6366f1" opacity="0.08"/>
  <rect x="110" y="130" width="180" height="130" rx="10" fill="#4338ca" stroke="#818cf8" stroke-width="3"/>
  <ellipse cx="200" cy="190" rx="60" ry="30" fill="#312e81" stroke="#6366f1" stroke-width="2"/>
  <path d="M170 190 Q200 130 230 190 Q220 220 180 210 Z" fill="#06b6d4" opacity="0.9"/>
  <text x="200" y="160" font-family="sans-serif" font-size="13" font-weight="800" fill="#ffffff" text-anchor="middle">NITRILE GLOVES</text>
  <text x="200" y="240" font-family="sans-serif" font-size="11" font-weight="600" fill="#a5b4fc" text-anchor="middle">100 PACK - POWDER FREE</text>
  <text x="200" y="330" font-family="sans-serif" font-size="14" font-weight="700" fill="#818cf8" text-anchor="middle">CHEMICAL RESISTANT</text>
</svg>''',

        'respirator.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_resp" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_resp)"/>
  <circle cx="200" cy="200" r="140" fill="#f97316" opacity="0.08"/>
  <path d="M140 160 Q200 120 260 160 Q270 230 240 280 Q200 300 160 280 Q130 230 140 160 Z" fill="#334155" stroke="#94a3b8" stroke-width="3"/>
  <path d="M155 165 Q200 145 245 165 Q250 205 200 215 Q150 205 155 165 Z" fill="#38bdf8" opacity="0.4" stroke="#0ea5e9" stroke-width="2"/>
  <circle cx="140" cy="240" r="26" fill="#f59e0b" stroke="#b45309" stroke-width="3"/>
  <circle cx="260" cy="240" r="26" fill="#f59e0b" stroke="#b45309" stroke-width="3"/>
  <line x1="140" y1="160" x2="100" y2="130" stroke="#475569" stroke-width="6" stroke-linecap="round"/>
  <line x1="260" y1="160" x2="300" y2="130" stroke="#475569" stroke-width="6" stroke-linecap="round"/>
  <text x="200" y="345" font-family="sans-serif" font-size="14" font-weight="700" fill="#f97316" text-anchor="middle">ORGANIC VAPOR RESPIRATOR</text>
</svg>''',

        'goggles.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_gog" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_gog)"/>
  <circle cx="200" cy="200" r="140" fill="#38bdf8" opacity="0.08"/>
  <path d="M80 180 Q140 140 200 170 Q260 140 320 180 Q325 240 270 250 Q200 260 200 220 Q200 260 130 250 Q75 240 80 180 Z" fill="#38bdf8" opacity="0.4" stroke="#0284c7" stroke-width="4"/>
  <line x1="80" y1="180" x2="40" y2="180" stroke="#475569" stroke-width="8" stroke-linecap="round"/>
  <line x1="320" y1="180" x2="360" y2="180" stroke="#475569" stroke-width="8" stroke-linecap="round"/>
  <text x="200" y="345" font-family="sans-serif" font-size="14" font-weight="700" fill="#38bdf8" text-anchor="middle">ANTI-SPLASH SAFETY GOGGLES</text>
</svg>''',

        'copper_sulfate.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_cuso4" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_cuso4)"/>
  <circle cx="200" cy="200" r="140" fill="#2563eb" opacity="0.08"/>
  <rect x="135" y="110" width="130" height="200" rx="14" fill="#1e293b" stroke="#2563eb" stroke-width="3"/>
  <rect x="165" y="75" width="70" height="35" rx="4" fill="#3b82f6"/>
  <rect x="150" y="160" width="100" height="120" rx="4" fill="#f8fafc" stroke="#2563eb" stroke-width="2"/>
  <text x="200" y="185" font-family="sans-serif" font-size="12" font-weight="800" fill="#1d4ed8" text-anchor="middle">COPPER(II)</text>
  <text x="200" y="202" font-family="sans-serif" font-size="11" font-weight="800" fill="#1e293b" text-anchor="middle">SULFATE</text>
  <text x="200" y="222" font-family="sans-serif" font-size="9" fill="#475569" text-anchor="middle">CuSO4 &middot; 5H2O</text>
  <text x="200" y="240" font-family="sans-serif" font-size="10" font-weight="bold" fill="#2563eb" text-anchor="middle">99% Blue Crystals</text>
</svg>''',

        'stirrer.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_stir" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_stir)"/>
  <circle cx="200" cy="200" r="140" fill="#ec4899" opacity="0.08"/>
  <rect x="110" y="190" width="180" height="110" rx="12" fill="#1e293b" stroke="#475569" stroke-width="3"/>
  <rect x="120" y="135" width="160" height="60" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2"/>
  <ellipse cx="200" cy="165" rx="40" ry="16" fill="none" stroke="#ef4444" stroke-width="2" opacity="0.6" stroke-dasharray="4 2"/>
  <circle cx="160" cy="245" r="18" fill="#334155" stroke="#06b6d4" stroke-width="2"/>
  <line x1="160" y1="245" x2="170" y2="235" stroke="#06b6d4" stroke-width="3" stroke-linecap="round"/>
  <text x="160" y="280" font-family="sans-serif" font-size="9" fill="#94a3b8" text-anchor="middle">SPEED</text>
  <circle cx="240" cy="245" r="18" fill="#334155" stroke="#ef4444" stroke-width="2"/>
  <line x1="240" y1="245" x2="248" y2="238" stroke="#ef4444" stroke-width="3" stroke-linecap="round"/>
  <text x="240" y="280" font-family="sans-serif" font-size="9" fill="#94a3b8" text-anchor="middle">HEAT</text>
  <text x="200" y="345" font-family="sans-serif" font-size="14" font-weight="700" fill="#ec4899" text-anchor="middle">MAGNETIC STIRRER</text>
</svg>''',

        'retort_stand.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <defs>
    <linearGradient id="bg_rtt" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" rx="24" fill="url(#bg_rtt)"/>
  <circle cx="200" cy="200" r="140" fill="#94a3b8" opacity="0.08"/>
  <rect x="120" y="310" width="160" height="25" rx="4" fill="#334155" stroke="#94a3b8" stroke-width="3"/>
  <line x1="160" y1="310" x2="160" y2="70" stroke="#cbd5e1" stroke-width="8"/>
  <rect x="150" y="160" width="20" height="20" rx="2" fill="#0284c7"/>
  <line x1="170" y1="170" x2="240" y2="170" stroke="#94a3b8" stroke-width="5"/>
  <circle cx="255" cy="170" r="18" fill="none" stroke="#94a3b8" stroke-width="5"/>
  <text x="200" y="370" font-family="sans-serif" font-size="14" font-weight="700" fill="#94a3b8" text-anchor="middle">RETORT STAND SUPPORT SET</text>
</svg>'''
    }

    for name, content in svgs.items():
        path = os.path.join(images_dir, name)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    print(f'Generated {len(svgs)} product images in {images_dir}')

if __name__ == '__main__':
    create_svgs()
