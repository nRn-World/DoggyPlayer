# Security Penetration Test Report

**Generated:** 2026-11-06 22:51:23 UTC

# Executive Summary

A white-box assessment of **Doggy Player**, a Windows Electron desktop media/IPTV player, identified **nine vulnerabilities**, including one **critical** and two **high** severity issues that together allow an attacker to take complete control of a user's computer and to steal their paid IPTV provider credentials.

**Overall risk posture:** High.

**Key findings**
- **Critical — remote code execution via missing navigation controls.** The application window runs with Node.js integration enabled and no restrictions on which web pages it may load. Because the app's core feature is playing URLs supplied by third-party IPTV providers, a hostile or hijacked provider URL that returns a web page instead of video can take over the window with full operating-system privileges. This was reproduced on a live Electron instance, as was the equivalent escalation through `window.open()`.
- **High — unrestricted request forgery from the app.** An internal bridge that fetches playlist and programme-guide data will fetch *any* address with any method, headers and body, and returns the response to the caller. This lets an attacker read services on the user's own machine and local network and exfiltrate the results.
- **High — cross-user IPTV credential theft.** The "create activation code" sharing feature uploads the user's full provider login (server, username, **password**) as plain base64 to a public third-party store, under a four-digit code. The entire code range can be swept in about two and a half minutes, exposing any user who has shared a code, and the same records can be overwritten to hijack a recipient's login.
- **Medium — five further issues** covering arbitrary local file read from the local media server, unvalidated playlist data controlling image request destinations, a hard-coded provider credential compiled into every build, an offline-recoverable operator credential, a cross-user sync-data overwrite, and markup injection in the statistics window.

**Business impact**
- Users' machines can be fully compromised through ordinary product use (opening a provider playlist), putting documents, saved credentials and the user's Windows account at risk.
- Paid IPTV subscriptions can be stolen from other customers, creating direct consumer harm, breach-notification exposure and reputational damage.
- A provider credential and an operator credential ship in the public build and must be treated as already compromised.

**Overarching remediation theme:** the application was built as if the player window were a trusted local component, but it displays content controlled by third parties. Restoring standard Electron isolation and adding a single, central policy for outbound URLs and for untrusted playlist data would close most of the surface at once. Detailed patches are included with each finding.

# Methodology

**Engagement type:** White-box source assessment with dynamic proof-of-concept validation, conducted against two provided source trees (the React renderer and the Electron main process). No production service or third-party data was modified.

**Scope**
- React/TypeScript renderer application, including playlist, programme-guide and provider-API ingestion.
- Electron main process: window creation, IPC handlers, local media server, ffmpeg pipeline, usage telemetry, and the auxiliary statistics window.

**Standards followed:** OWASP Application Security Verification Standard and Web Security Testing Guide; OWASP Top 10 for desktop and client applications; the official Electron security checklist. Static review and dynamic validation were combined so that every reported issue rests on an observed result rather than a source-code hypothesis.

**Activities performed**
- Threat modelling of trust boundaries across the renderer, main process, local media server and third-party content sources.
- Full static-analysis baseline over both trees: semantic pattern scanning, structural AST search, secret detection with two independent scanners, and dependency/configuration scanning.
- Manual review of every IPC channel, every process-spawn site, every filesystem sink and every network call.
- Extraction of the real handler and route logic into standalone harnesses and reproduction of each issue: a live request-forgery bridge against an isolated loopback service, the media server against a real ffmpeg build, the playlist parser against hostile playlists, and the Electron window policy against a real Electron runtime, each with a negative control.
- End-to-end verification of the credential-sharing exposure against the live third-party store using only self-created records, and measurement of enumeration throughput.
- Bypass review and behavioural regression checks for every proposed fix.

**Constraints**
- Only the two source directories were supplied; the project manifest, build configuration and dependency lockfile were not available. Consequently no dependency-CVE reporting could be performed, and proposed patches could not be passed through the project's own type checker, build or test suite. Both limitations are disclosed in the individual findings rather than presented as clean results.

# Technical Analysis

**Severity model** reflects demonstrated exploitability against demonstrated impact. Every reported finding was reproduced; severities were set from what the proof of concept achieved, not from the worst case that might be imagined from it.

1. **Missing navigation and window-open controls with Node integration (Critical).** The main window is created with `nodeIntegration: true`, `contextIsolation: false` and `webSecurity: false`, and registers no `will-navigate`, `will-redirect` or `setWindowOpenHandler` guard. A foreign-origin document navigated into that window, or opened as a child window, retains full Node.js capability. Reproduced on a live Electron runtime, including reading local files from the foreign document and confirming that child windows inherit the weakened preferences. Because the product's primary function is loading third-party URLs, this is reachable through normal use.

2. **Unrestricted request forgery in the data-fetching bridge (High).** The `iptv-fetch` IPC handler forwards a caller-supplied URL, method, headers and body to `fetch` with no scheme allowlist, no address filtering and default redirect following, and returns the body. Validated against a loopback-only service holding a secret: the secret was returned and exfiltrated, alternate loopback notations all worked, and a redirect was followed into the internal service. Negative control: non-HTTP schemes are rejected by the runtime, which bounds the impact to HTTP(S).

3. **Cross-user credential disclosure in the activation-code feature (High).** Credentials are base64-encoded, not encrypted, and published to a public store under a four-digit key with no secret component. A full sweep of the identifier space was performed against the live store using only self-planted records, confirming unauthenticated read and write and quantifying enumeration at roughly two and a half minutes for the whole space. The same weakness affects the favourites sync, which uses a fully derivable identifier to store per-user data (Medium).

4. **Local file read in the loopback media server (Medium).** The `/stream` route passes the `path` parameter straight to a file read with no containment; the random token is the only control and is printed to the console. Verified with the route extracted and a real ffmpeg build: `/etc/passwd` returned in full, byte-range requests allowed arbitrary offsets.

5. **Untrusted playlist data reaching request sinks (Medium).** The playlist parser copies logo URLs and labels into application state unvalidated, and the logo is bound to a live image source. A hostile playlist therefore chooses the scheme and host of requests made by a privileged window; confirmed in a headless browser.

6. **Shipped and recoverable secrets (Medium).** A complete provider credential is hard-coded in the renderer and compiled into every build; the statistics gate authenticates against unsalted digests shipped in the source, and the username digest matches a public wordlist entry, so the gate credential is recoverable offline.

7. **Markup injection in the statistics window (Low).** Chart rendering interpolates its data into an HTML template. Breakout was demonstrated in a browser, but the data is currently generated locally, so reachability as an attack is limited; it is recorded because the window holds Node privileges.

**Systemic themes**
- **Untrusted content treated as trusted UI:** the architecture assumes anything rendered in the player window is benign, but the window displays third-party-controlled content.
- **No central egress policy:** outbound requests are made from several places without any single place that decides which destinations are acceptable.
- **Client-side secrets and identifiers:** shipped credentials, unsalted password digests, and short numeric identifiers used as if they were secrets.
- **Defence in depth absent:** no containment on filesystem paths, no scheme validation on playlist-supplied URLs, and no process isolation for the renderer.

**Cross-finding chaining.** The critical navigation issue is the escalation multiplier for the rest: any primitive that can place attacker-authored content into the window, or steer it to an attacker origin, converts into full code execution. The request-forgery bridge supplies the network reach, and the credential exposure supplies the loot. The most realistic end-to-end path begins with a hostile playlist or provider response and ends in full account compromise.

**Areas reviewed and cleared**
- No raw-HTML injection sinks exist in the main renderer; playlist, programme-guide and subtitle content render as escaped text, and hostile markup and entity-expansion payloads were tested and did not execute.
- Process spawning uses argument arrays with no shell anywhere, and argument-smuggling and protocol-abuse attempts against the media pipeline were tested and did not change what was executed.
- Stream-token disclosure to a third party was tested in both directions and blocked by browser referrer policy and private-network protections; the media server's redirect branch is unreachable from generated URLs; cache path construction is derived from hashes and contained; and a shell-string interpolation of a process identifier was verified numerically safe.
- Command-line argument evaluation was tested with break-out payloads and round-trips as inert data.

# Recommendations

**Immediate**
1. **Restore the Electron security posture for every window, including the statistics window.** Disable Node.js integration, enable context isolation and the renderer sandbox, and re-enable web security. Expose only the specific capabilities the renderer needs through a narrow preload bridge. This single change removes the most severe consequence of every other renderer-side finding.
2. **Add an explicit navigation policy.** Cancel navigation to any origin other than the packaged application document or the development server, and deny all new windows. Both parts are required: a navigation guard alone is bypassed by `window.open()`, which inherits the parent's preferences.
3. **Put a central allowlist in front of all outbound requests.** Permit only HTTP and HTTPS, resolve the destination and reject loopback, private, link-local, carrier-grade-NAT, multicast and cloud-metadata addresses, and disable or re-validate automatic redirects on every hop.
4. **Withdraw the activation-code feature until it is redesigned.** Replace the four-digit identifier with a high-entropy random token, encrypt the payload with a key derived from a secret the sharing user transmits out of band, add expiry and revocation, and treat all previously shared codes as already compromised.
5. **Rotate the hard-coded provider credential and the statistics-gate credential**, and remove both from the source. Replace the gate with a properly salted, high-iteration password hash, or move the check server-side.

**Short-term**
6. **Confine local file access.** Resolve media paths to canonical absolute paths and verify they remain inside permitted roots before any read or transcode; support an optional user-configured media library root instead of unrestricted paths.
7. **Validate all playlist-supplied data at parse time.** Allow only HTTP and HTTPS URLs, discard unexpected schemes such as `data:` and `file:`, strip markup from labels, and treat every playlist field as untrusted text.
8. **Replace the shared sync identifiers.** Derive sync keys from a per-installation secret rather than from the provider URL and username, so records cannot be located or overwritten from public information.
9. **Stop logging media URLs and stream tokens**, since the token's confidentiality is currently the only protection on the media server.

**Medium-term**
10. **Adopt a security regression gate for desktop builds:** add automated checks for the Electron security checklist (preferences, navigation handlers, per-channel IPC validation) and a content-security policy for both windows, so weakened preferences cannot be reintroduced unnoticed.
11. **Supply the project manifest and lockfile** so dependency risk can be assessed; none of the bundled frameworks or the update mechanism could be reviewed for known vulnerabilities from source alone.
12. **Review the auto-update trust model** end to end, including feed selection and update signature verification, which could not be assessed without the packaging configuration.

**Retest and validation:** re-run the request-forgery reproduction, the media-server file-read reproduction, the hostile-playlist reproduction and the Electron window-policy reproduction after remediation to confirm each control holds. Priority should go to the critical navigation issue and the credential-sharing exposure, as both affect users in ordinary operation.

