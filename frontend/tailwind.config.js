module.exports = {
  darkMode: "class",
  content: ["./*.html"],
  theme: {
    extend: {
      colors: {
        "background": "#f8f9fa",
        "surface-container-highest": "#e1e3e4",
        "on-surface-variant": "#4d4635",
        "inverse-surface": "#2e3132",
        "on-secondary-fixed": "#1a1c1e",
        "on-primary": "#ffffff",
        "surface-variant": "#e1e3e4",
        "secondary-container": "#e2e2e5",
        "error": "#ba1a1a",
        "tertiary-container": "#aeb4b2",
        "on-error": "#ffffff",
        "on-tertiary-container": "#404644",
        "inverse-primary": "#e9c349",
        "tertiary-fixed-dim": "#c2c8c5",
        "primary-fixed": "#ffe088",
        "on-background": "#191c1d",
        "secondary": "#5d5e61",
        "on-tertiary": "#ffffff",
        "surface-tint": "#735c00",
        "on-tertiary-fixed": "#171d1b",
        "on-primary-fixed": "#241a00",
        "surface-container-lowest": "#ffffff",
        "on-secondary-container": "#636467",
        "surface-container-high": "#e7e8e9",
        "outline-variant": "#d0c5af",
        "secondary-fixed-dim": "#c6c6c9",
        "surface": "#f8f9fa",
        "primary-fixed-dim": "#e9c349",
        "outline": "#7f7663",
        "on-primary-container": "#554300",
        "surface-container": "#edeeef",
        "primary-container": "#d4af37",
        "surface-container-low": "#f3f4f5",
        "on-surface": "#191c1d",
        "error-container": "#ffdad6",
        "on-error-container": "#93000a",
        "tertiary": "#5a605e",
        "inverse-on-surface": "#f0f1f2",
        "on-primary-fixed-variant": "#574500",
        "surface-dim": "#d9dadb",
        "primary": "#735c00",
        "tertiary-fixed": "#dee4e1",
        "secondary-fixed": "#e2e2e5",
        "on-tertiary-fixed-variant": "#424846",
        "on-secondary": "#ffffff",
        "surface-bright": "#f8f9fa",
        "on-secondary-fixed-variant": "#454749"
      },
      borderRadius: {
        "DEFAULT": "0.125rem",
        "lg": "0.25rem",
        "xl": "0.5rem",
        "full": "0.75rem"
      },
      spacing: {
        "base": "4px",
        "xl": "32px",
        "sm": "8px",
        "gutter": "20px",
        "xs": "4px",
        "lg": "24px",
        "sidebar-width": "260px",
        "md": "16px"
      },
      fontFamily: {
        "title-lg": ["Inter"],
        "headline-md": ["Inter"],
        "label-md": ["Inter"],
        "headline-sm": ["Inter"],
        "data-mono": ["Inter"],
        "body-sm": ["Inter"],
        "body-md": ["Inter"],
        "display-lg": ["Inter"]
      },
      fontSize: {
        "title-lg": ["18px", {"lineHeight": "24px", "fontWeight": "600"}],
        "headline-md": ["24px", {"lineHeight": "32px", "letterSpacing": "-0.01em", "fontWeight": "600"}],
        "label-md": ["12px", {"lineHeight": "16px", "letterSpacing": "0.05em", "fontWeight": "600"}],
        "headline-sm": ["20px", {"lineHeight": "28px", "fontWeight": "600"}],
        "data-mono": ["14px", {"lineHeight": "20px", "fontWeight": "500"}],
        "body-sm": ["14px", {"lineHeight": "20px", "fontWeight": "400"}],
        "body-md": ["16px", {"lineHeight": "24px", "fontWeight": "400"}],
        "display-lg": ["32px", {"lineHeight": "40px", "letterSpacing": "-0.02em", "fontWeight": "700"}]
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries')
  ]
};
