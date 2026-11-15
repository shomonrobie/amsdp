/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      // Identity & Access
      { source: '/api/v1/staff/:path*', destination: 'http://identity:8000/api/v1/staff/:path*' },
      // Organization
      { source: '/api/v1/orgs/:path*', destination: 'http://organization:8001/api/v1/orgs/:path*' },
      // Scheduling — a branch's clinic sessions. Must precede the generic
      // /api/v1/branches rule below, which would otherwise send this to the
      // organization service (where it does not exist).
      { source: '/api/v1/branches/:branchId/sessions', destination: 'http://scheduling:8004/api/v1/branches/:branchId/sessions' },
      // Organization — facility records addressed by their own id. The list and
      // create routes live under /branches and are covered below; editing or
      // retiring a floor/department/room/speciality uses these paths, which
      // would otherwise 404 at this proxy.
      { source: '/api/v1/floors/:path*', destination: 'http://organization:8001/api/v1/floors/:path*' },
      { source: '/api/v1/departments/:path*', destination: 'http://organization:8001/api/v1/departments/:path*' },
      { source: '/api/v1/rooms/:path*', destination: 'http://organization:8001/api/v1/rooms/:path*' },
      { source: '/api/v1/specialties/:path*', destination: 'http://organization:8001/api/v1/specialties/:path*' },
      { source: '/api/v1/branches/:path*', destination: 'http://organization:8001/api/v1/branches/:path*' },
      // Authenticated user's branch context
      { source: '/api/v1/me/:path*', destination: 'http://organization:8001/api/v1/me/:path*' },
      // Patient
      { source: '/api/v1/patients/:path*', destination: 'http://patient:8002/api/v1/patients/:path*' },
      // Doctor
      { source: '/api/v1/doctors/:path*', destination: 'http://doctor:8003/api/v1/doctors/:path*' },
      // Scheduling
      { source: '/api/v1/schedules/:path*', destination: 'http://scheduling:8004/api/v1/schedules/:path*' },
      // Scheduling — a single clinic session (edit / retire)
      { source: '/api/v1/sessions/:path*', destination: 'http://scheduling:8004/api/v1/sessions/:path*' },
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