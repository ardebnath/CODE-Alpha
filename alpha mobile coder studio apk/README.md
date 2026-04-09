# Alpha Mobile Coder Studio APK

This folder is a separate Android app project for Alpha Studio.

It is designed to look and behave like the main browser studio by:
- embedding the same `index.html`, `style.css`, and `studio.js`
- starting a local Alpha HTTP server inside the app on `127.0.0.1`
- storing user accounts, projects, history, packages, and the Alpha database in the phone's private app data folder

## What Is Included

- a real Android Studio project in `app/`
- a WebView shell which opens the embedded Alpha Studio
- embedded Python runtime source for the Alpha interpreter
- local account/project save and load support on the phone
- the same starter programs, guide, history, package manager, and browser studio layout as the main Alpha Studio

## Important Build Note

This machine did not have a working Android SDK, Java, or Gradle toolchain available on April 8, 2026, so a compiled `.apk` could not be honestly generated here.

The project is ready for Android Studio. After the Android toolchain is available, the debug APK will usually appear at:

`app/build/outputs/apk/debug/app-debug.apk`

## How To Build The APK

1. Open this folder in Android Studio.
2. Let Android Studio install or update the required SDK and Gradle parts.
3. If Android Studio asks to upgrade plugin versions, accept the safe upgrade.
4. Build `app` with `Build > Build APK(s)`.
5. Copy the generated `.apk` from `app/build/outputs/apk/debug/` to your phone and install it.

## Phone Data Storage

Inside the app, Alpha stores:
- user accounts
- saved projects
- package registry
- Alpha database
- run history

All of that stays inside the phone app's private storage.

## Known Mobile Limits

- core Alpha studio features are included
- desktop-only GUI modules such as `turtle` may not work on Android the same way they do on a PC
- the WebView app uses the same browser studio layout, but wrapped inside a native Android app
