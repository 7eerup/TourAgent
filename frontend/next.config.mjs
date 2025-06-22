/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    // CORS 없이 네이버 Open API 호출을 위한 프록시 설정
    async rewrites() {
        return [
        {
            source: '/naver/local',
            destination: 'https://openapi.naver.com/v1/search/local.json',
        },
        {
            source: '/naver/image',
            destination: 'https://openapi.naver.com/v1/search/image.json',
        },
        ];
    },
};

export default nextConfig;
