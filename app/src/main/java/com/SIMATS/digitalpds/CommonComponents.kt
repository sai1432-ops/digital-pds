package com.SIMATS.digitalpds

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.sp
import com.SIMATS.digitalpds.ui.theme.PrimaryBlue

@Composable
fun InitialsAvatar(
    name: String,
    modifier: Modifier = Modifier,
    backgroundColor: Color = Color(0xFFE9EEF3),
    textColor: Color = PrimaryBlue,
    fontSize: TextUnit = 20.sp
) {
    val initial = name.firstOrNull()?.uppercase() ?: "?"
    Box(
        modifier = modifier
            .clip(CircleShape)
            .background(backgroundColor),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = initial.toString(),
            color = textColor,
            fontSize = fontSize,
            fontWeight = FontWeight.Bold
        )
    }
}
