// stealth.js — hide headless browser fingerprint
// Based on puppeteer-extra-plugin-stealth techniques

// Target UA components — keep consistent across all overrides
const CHROME_VERSION = '131.0.0.0';
const CHROME_MAJOR = '131';
const PLATFORM = 'Win32';
const PLATFORM_UA = 'Windows NT 10.0; Win64; x64';

// 1. Remove webdriver flag (primary bot detection signal)
Object.defineProperty(navigator, 'webdriver', {
  get: () => undefined,
});

// 2. Override plugins with proper PluginArray-like object
(function() {
  const pluginData = [
    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format', mimeTypes: ['application/x-google-chrome-pdf'] },
    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '', mimeTypes: ['application/pdf'] },
    { name: 'Native Client', filename: 'internal-nacl-plugin', description: '', mimeTypes: [] },
  ];

  function FakePlugin(data) {
    this.name = data.name;
    this.filename = data.filename;
    this.description = data.description;
    this.length = data.mimeTypes.length;
  }
  FakePlugin.prototype[Symbol.iterator] = function*() {};

  const fakePlugins = pluginData.map(d => new FakePlugin(d));

  Object.defineProperty(navigator, 'plugins', {
    get: () => {
      const arr = fakePlugins;
      arr.item = i => arr[i] || null;
      arr.namedItem = name => arr.find(p => p.name === name) || null;
      arr.refresh = () => {};
      arr.length = fakePlugins.length;
      return arr;
    },
  });
})();

// 3. Override mimeTypes
Object.defineProperty(navigator, 'mimeTypes', {
  get: () => {
    const mimeTypes = [
      { type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format', enabledPlugin: navigator.plugins[1] },
      { type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format', enabledPlugin: navigator.plugins[0] },
    ];
    mimeTypes.item = i => mimeTypes[i] || null;
    mimeTypes.namedItem = name => mimeTypes.find(m => m.type === name) || null;
    mimeTypes.length = 2;
    return mimeTypes;
  },
});

// 4. Languages
Object.defineProperty(navigator, 'languages', {
  get: () => ['en-US', 'en'],
});

// 5. Platform — consistent with Windows Chrome UA
Object.defineProperty(navigator, 'platform', {
  get: () => PLATFORM,
});

// 6. Hardware concurrency
Object.defineProperty(navigator, 'hardwareConcurrency', {
  get: () => 8,
});

// 7. Device memory
Object.defineProperty(navigator, 'deviceMemory', {
  get: () => 8,
});

// 8. Max touch points — 0 for desktop
Object.defineProperty(navigator, 'maxTouchPoints', {
  get: () => 0,
});

// 9. window.chrome object — missing in headless
window.chrome = {
  app: {
    isInstalled: false,
    InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
    RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' },
  },
  runtime: {
    OnInstalledReason: { CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update' },
    OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' },
    PlatformArch: { ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
    PlatformNaclArch: { ARM: 'arm', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
    PlatformOs: { ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win' },
    RequestUpdateCheckStatus: { NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available' },
    connect: function() {},
    sendMessage: function() {},
  },
};

// 10. Permissions API — make "notifications" return "prompt" instead of "denied"
if (window.Notification) {
  Notification.permission = 'default';
}

const originalPermissionsQuery = navigator.permissions?.query;
if (originalPermissionsQuery) {
  navigator.permissions.query = function(parameters) {
    if (parameters.name === 'notifications') {
      return Promise.resolve({ state: 'prompt', onchange: null });
    }
    return originalPermissionsQuery.call(this, parameters);
  };
}

// 11. WebGL vendor/renderer — hide SwiftShader (headless indicator)
const WEBGL_VENDOR = 'Google Inc. (NVIDIA)';
const WEBGL_RENDERER = 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0, D3D11)';

const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
  if (parameter === 37445) return WEBGL_VENDOR;
  if (parameter === 37446) return WEBGL_RENDERER;
  return getParameter.call(this, parameter);
};

if (typeof WebGL2RenderingContext !== 'undefined') {
  const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
  WebGL2RenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return WEBGL_VENDOR;
    if (parameter === 37446) return WEBGL_RENDERER;
    return getParameter2.call(this, parameter);
  };
}

// 12. Connection API — typical broadband
Object.defineProperty(navigator, 'connection', {
  get: () => ({
    effectiveType: '4g',
    rtt: 50,
    downlink: 10,
    saveData: false,
  }),
});

// 13. userAgentData (Client Hints API) — override to match our UA
if (navigator.userAgentData) {
  const brands = [
    { brand: 'Google Chrome', version: CHROME_MAJOR },
    { brand: 'Chromium', version: CHROME_MAJOR },
    { brand: 'Not_A Brand', version: '24' },
  ];
  const fullVersionList = [
    { brand: 'Google Chrome', version: CHROME_VERSION },
    { brand: 'Chromium', version: CHROME_VERSION },
    { brand: 'Not_A Brand', version: '24.0.0.0' },
  ];

  Object.defineProperty(navigator, 'userAgentData', {
    get: () => ({
      brands: brands,
      mobile: false,
      platform: 'Windows',
      getHighEntropyValues: function(hints) {
        return Promise.resolve({
          architecture: 'x86',
          bitness: '64',
          brands: brands,
          fullVersionList: fullVersionList,
          mobile: false,
          model: '',
          platform: 'Windows',
          platformVersion: '10.0.0',
          uaFullVersion: CHROME_VERSION,
          wow64: false,
        });
      },
      toJSON: function() {
        return { brands: brands, mobile: false, platform: 'Windows' };
      },
    }),
  });
}

// 14. Prevent iframe detection of automation
const originalContentWindow = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow');
if (originalContentWindow) {
  Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
    get: function() {
      const iframe = originalContentWindow.get.call(this);
      if (iframe) {
        try {
          Object.defineProperty(iframe.navigator, 'webdriver', { get: () => undefined });
        } catch (e) {}
      }
      return iframe;
    },
  });
}

// 15. Override Intl.DateTimeFormat to be consistent
// (timezone is already UTC in Docker, this is fine for Cyprus browsing)

// 16. Prevent detection via toString() on overridden functions
// Make native function toString return "[native code]"
const nativeToString = Function.prototype.toString;
const overriddenFns = new Set();

function makeNative(fn) {
  overriddenFns.add(fn);
}

Function.prototype.toString = function() {
  if (overriddenFns.has(this)) {
    return 'function ' + (this.name || '') + '() { [native code] }';
  }
  return nativeToString.call(this);
};

makeNative(Function.prototype.toString);

// Mark our overridden functions as "native"
if (navigator.permissions?.query) makeNative(navigator.permissions.query);
makeNative(WebGLRenderingContext.prototype.getParameter);
if (typeof WebGL2RenderingContext !== 'undefined') {
  makeNative(WebGL2RenderingContext.prototype.getParameter);
}
