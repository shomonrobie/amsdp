/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      // Identity & Access
      { source: '/api/v1/staff/:path*', destination: 'http://identity:8000/api/v1/staff/:path*' },
      // Organization
      { source: '/api/v1/orgs/:path*', destination: 'http://organization:8001/api/v1/orgs/:path*' },
      { source: '/api/v1/branches/:path*', destination: 'http://organization:8001/api/v1/branches/:path*' },
      // Authenticated user's branch context
      { source: '/api/v1/me/:path*', destination: 'http://organization:8001/api/v1/me/:path*' },
      // Patient
      { source: '/api/v1/patients/:path*', destination: 'http://patient:8002/api/v1/patients/:path*' },
      // Doctor
      { source: '/api/v1/doctors/:path*', destination: 'http://doctor:8003/api/v1/doctors/:path*' },
      // Scheduling
      { source: '/api/v1/schedules/:path*', destination: 'http://scheduling:8004/api/v1/schedules/:path*' },
      // Appointment
      { source: '/api/v1/appointments/:path*', destination: 'http://appointment:8005/api/v1/appointments/:path*' },
      // Dashboard (metrics + audit search)
      { source: '/api/v1/dashboard/:path*', destination: 'http://appointment:8005/api/v1/dashboard/:path*' },
      // Queue
      { source: '/api/v1/queue/:path*', destination: 'http://queuing:8006/api/v1/queue/:path*' },
      // PQT (tracking) — public, no auth
      { source: '/track/:path*', destination: 'http://appointment:8005/api/v1/track/:path*' },
      // Audit
      { source: '/api/v1/audit/:path*', destination: 'http://audit:8007/api/v1/audit/:path*' },
    ];
  },
};
module.exports = nextConfig;