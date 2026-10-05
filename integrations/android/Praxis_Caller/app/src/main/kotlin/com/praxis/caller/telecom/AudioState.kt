package com.praxis.caller.telecom

data class AudioRoute(val id: String, val label: String, val speaker: Boolean = false)
data class AudioState(
    val muted: Boolean? = null,
    val routes: List<AudioRoute> = emptyList(),
    val selected: String? = null,
    val error: String? = null,
)
