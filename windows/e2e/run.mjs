const CHECK_NAME = 'windows_extension_model_e2e';

// Production uses a randomized pipe that accepts only the exact
// service-launched user agent after PID/session/path/signature validation and
// an inherited-secret handshake. A Node test process must not impersonate that
// boundary. Keep the legacy entrypoint honest until the optional Windows matrix
// has an external UI/outcome observation harness.
const result = {
  check: CHECK_NAME,
  status: 'pending',
  reason_code: process.platform === 'win32'
    ? 'trusted_agent_ipc_requires_external_observation_harness'
    : 'windows_required',
};

console.log(JSON.stringify(result));
