# Alpha Source, Proprietary Use, and Protection Guide

## 1. What This Guide Explains

This guide explains:
- what Alpha's current source status is
- what people may do for learning and evaluation
- what should require written permission
- why browser code still cannot be fully hidden
- why older public releases may still need separate legal review

## 2. Current Project Decision

Alpha is now described in this repository as:
- proprietary / brand property of `Bluear_cod`
- source-available for learning and review
- restricted for business use, large-project use, and copying of core code without permission

Read these files together:
- `LICENSE`
- `NOTICE`
- `Commercial Use, Credit, and Source Protection Policy.md`

## 3. What This Means In Practice

Allowed without a separate written license:
- personal learning
- education
- private evaluation
- non-commercial testing

Not allowed without prior written permission:
- commercial use
- client work
- enterprise or production deployment
- copying or republishing core Alpha code
- rebranding the core Alpha code as another main product

## 4. Credit Requirement

Visible credit should be kept for:

`Alpha by Bluear_cod`

Recommended credit line:

`Powered by Alpha by Bluear_cod`

## 5. Can The HTML Runner Be Hidden Or Encrypted?

Short answer: no, not really.

If code runs in the user's browser, the browser must receive it.
That means files like:
- `index.html`
- `style.css`
- `studio.js`

can still be viewed through browser developer tools, saved from the network tab, or copied after page load.

You can:
- minify browser code
- compress browser code
- obfuscate browser code

But you cannot make browser code truly secret if the browser must run it.

## 6. Can The Python Files Be Hidden?

Yes, but only if you do not distribute them.

### If Alpha Runs Only On Your Own Server

Then the Python files can stay private because users do not download them directly.

### If You Give The Python Program To Other People

Then the code is no longer truly private.

Even if you:
- package it
- freeze it into an `.exe`
- obfuscate it

determined users may still inspect or recover much of the logic.

## 7. Best Protection Model

If `Bluear_cod` wants stronger protection later:

1. Keep public learning materials readable.
2. Keep sensitive business logic on the server side.
3. Do not rely on browser secrecy.
4. Treat obfuscation only as a delay, not as true protection.
5. Use written commercial licenses for paid or business use.

## 8. Important Public Release Warning

Important:
- changing the repository's current license text does not automatically erase every right already granted under older public releases
- earlier public copies, forks, or downloaded versions may need separate legal review
- if strong enforcement matters, `Bluear_cod` should get qualified legal advice

## 9. Final Source Model

For the current repository wording:
- Alpha is no longer described as open source
- Alpha is branded proprietary / brand property of `Bluear_cod`
- learning and evaluation use are allowed
- business or large-scale use should require written paid permission
- browser code still cannot be truly hidden
- server-side deployment is still the best path for stronger control
