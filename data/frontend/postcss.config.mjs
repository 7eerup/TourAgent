// const config = {
//   plugins: ["@tailwindcss/postcss"],
// };

// export default config;


// postcss.config.mjs
import tailwindcss from 'tailwindcss';      // Tailwind CSS 플러그인
import autoprefixer from 'autoprefixer';    // 벤더 프리픽스 자동 추가 플러그인

export default {
  plugins: {
    // 반드시 모듈 참조 형태로 등록해야 인식됩니다
    tailwindcss: {},
    autoprefixer: {},
  },
};