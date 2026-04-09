package com.bluearcod.alphamobilecoderstudio

import android.annotation.SuppressLint
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private lateinit var startupOverlay: View
    private lateinit var startupTitle: TextView
    private lateinit var startupMessage: TextView
    private lateinit var progressBar: ProgressBar
    private lateinit var retryButton: Button

    private val startupExecutor = Executors.newSingleThreadExecutor()
    private var studioUrl: String? = null
    private var loadingFailed = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        bindViews()
        configureWebView()

        retryButton.setOnClickListener {
            startAlphaStudio()
        }

        onBackPressedDispatcher.addCallback(
            this,
            object : OnBackPressedCallback(true) {
                override fun handleOnBackPressed() {
                    if (webView.canGoBack()) {
                        webView.goBack()
                        return
                    }
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            },
        )

        startAlphaStudio()
    }

    private fun bindViews() {
        webView = findViewById(R.id.webView)
        startupOverlay = findViewById(R.id.startupOverlay)
        startupTitle = findViewById(R.id.startupTitle)
        startupMessage = findViewById(R.id.startupMessage)
        progressBar = findViewById(R.id.progressBar)
        retryButton = findViewById(R.id.retryButton)
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun configureWebView() {
        webView.setBackgroundColor(Color.TRANSPARENT)
        webView.isVerticalScrollBarEnabled = false
        webView.isHorizontalScrollBarEnabled = false
        webView.webChromeClient = WebChromeClient()

        val settings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.databaseEnabled = true
        settings.loadsImagesAutomatically = true
        settings.allowFileAccess = false
        settings.allowContentAccess = false
        settings.cacheMode = WebSettings.LOAD_DEFAULT
        settings.loadWithOverviewMode = true
        settings.useWideViewPort = true
        settings.setSupportZoom(true)
        settings.displayZoomControls = false
        settings.builtInZoomControls = false
        settings.safeBrowsingEnabled = true
        settings.mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW

        webView.webViewClient =
            object : WebViewClient() {
                override fun shouldOverrideUrlLoading(
                    view: WebView,
                    request: WebResourceRequest,
                ): Boolean {
                    val requestUri = request.url
                    val localHost = studioUrl?.let { Uri.parse(it).host }
                    val requestHost = requestUri.host

                    if (request.isForMainFrame && localHost != null && requestHost != localHost) {
                        startActivity(Intent(Intent.ACTION_VIEW, requestUri))
                        return true
                    }

                    return false
                }

                override fun onPageFinished(view: WebView, url: String) {
                    super.onPageFinished(view, url)
                    if (!loadingFailed) {
                        showContent(
                            title = getString(R.string.loading_ready_title),
                            message = getString(R.string.loading_ready_message),
                        )
                    }
                }

                override fun onReceivedError(
                    view: WebView,
                    request: WebResourceRequest,
                    error: WebResourceError,
                ) {
                    super.onReceivedError(view, request, error)
                    if (!request.isForMainFrame) {
                        return
                    }
                    showFailure(
                        title = getString(R.string.loading_failed_title),
                        message = error.description?.toString()
                            ?: getString(R.string.loading_failed_message),
                    )
                }
            }
    }

    private fun startAlphaStudio() {
        loadingFailed = false
        showLoading(
            title = getString(R.string.loading_title),
            message = getString(R.string.loading_message),
        )

        startupExecutor.execute {
            try {
                if (!Python.isStarted()) {
                    Python.start(AndroidPlatform(applicationContext))
                }

                val python = Python.getInstance()
                val hostModule = python.getModule("android_mobile_host")
                val localUrl = hostModule.callAttr(
                    "start_server",
                    filesDir.absolutePath,
                    8135,
                ).toString()

                studioUrl = localUrl
                runOnUiThread {
                    webView.loadUrl(localUrl)
                }
            } catch (error: Exception) {
                runOnUiThread {
                    showFailure(
                        title = getString(R.string.loading_failed_title),
                        message = error.message ?: getString(R.string.loading_failed_message),
                    )
                }
            }
        }
    }

    private fun showLoading(title: String, message: String) {
        startupOverlay.visibility = View.VISIBLE
        startupTitle.text = title
        startupMessage.text = message
        progressBar.visibility = View.VISIBLE
        retryButton.visibility = View.GONE
    }

    private fun showContent(title: String, message: String) {
        startupTitle.text = title
        startupMessage.text = message
        progressBar.visibility = View.GONE
        retryButton.visibility = View.GONE
        startupOverlay.animate()
            .alpha(0f)
            .setDuration(220L)
            .withEndAction {
                startupOverlay.visibility = View.GONE
                startupOverlay.alpha = 1f
            }
            .start()
    }

    private fun showFailure(title: String, message: String) {
        loadingFailed = true
        startupOverlay.visibility = View.VISIBLE
        startupTitle.text = title
        startupMessage.text = message
        progressBar.visibility = View.GONE
        retryButton.visibility = View.VISIBLE
    }

    override fun onDestroy() {
        super.onDestroy()
        startupExecutor.shutdownNow()
        webView.destroy()
    }
}
