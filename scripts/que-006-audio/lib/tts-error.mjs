/**
 * The one error shape every TTS provider raises.
 *
 * `generate.mjs` retries on `retryable`, stops the whole run on `stopRun`, and
 * shows `guidance` to a human. Those three decisions must not depend on which
 * provider produced the failure, so both clients throw this type instead of
 * each having its own class the caller has to know about.
 *
 * `provider` is carried so a message can name the service that refused, and so
 * a mixed run can never mistake one provider's failure for another's.
 */

export class TtsError extends Error {
  /**
   * @param {string} message
   * @param {{kind?: string, provider?: string|null, status?: number|null,
   *   retryable?: boolean, stopRun?: boolean, guidance?: string,
   *   detail?: string}} [info]
   */
  constructor(message, info = {}) {
    super(message);
    this.name = 'TtsError';
    this.kind = info.kind || 'unknown';
    this.provider = info.provider || null;
    this.status = info.status ?? null;
    this.retryable = Boolean(info.retryable);
    this.stopRun = Boolean(info.stopRun);
    this.guidance = info.guidance || '';
    this.detail = info.detail || '';
  }
}
