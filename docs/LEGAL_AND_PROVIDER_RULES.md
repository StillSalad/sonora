# PROVIDER, COPYRIGHT & COMPLIANCE CHECKLIST

This document is an engineering checklist, not legal advice. Obtain legal review before
public launch or commercial use.

## General
- Do not scrape websites or extract audio without permission.
- Do not bypass DRM, paywalls, geographical restrictions or access controls.
- Do not host copyrighted recordings without the necessary licenses.
- Do not assume that public metadata means unrestricted artwork or preview rights.
- Store provider attribution and comply with each provider's branding/display rules.
- Check commercial-use terms, caching restrictions, territory restrictions and rate limits.
- Implement takedown/contact process and preserve audit records.

## Preview rights
For every preview source, record:
- provider and exact API/product;
- applicable terms and documentation version/date;
- allowed territories;
- maximum duration and playback conditions;
- whether caching is allowed;
- expiry and revocation process;
- required attribution and links.

If any field is uncertain, mark RIGHTS_PENDING and do not play the audio.

## Provider-specific engineering caution
- Spotify: do not rely on deprecated preview_url; verify current Spotify developer terms,
  approved use cases, display requirements and restrictions before adding any account feature.
- Apple Music: use MusicKit and Apple Music API only within current authorization and
  subscription/territory requirements.
- MusicBrainz: metadata source; obey its public API rate limits, identify the application,
  and review licensing/attribution and commercial terms.
- YouTube Music: do not assume an official public API for every desired operation.
  Use permitted external links or officially supported integrations only.
- Lyra: implement only against an API or URL scheme supplied and documented by its owner.

## Privacy
- GDPR transparency, data minimization, lawful basis, consent where required.
- Export and deletion workflows.
- Retention schedule and security incident plan.
- OAuth scopes limited to required actions.
- Token secrets encrypted and never shipped to frontend.
- Age-appropriate community design, reporting and moderation.
