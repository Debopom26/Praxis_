package com.praxis.caller.praxis
import com.praxis.caller.ui.praxis.riskColor
import org.junit.Assert.*
import org.junit.Test
class RiskColorTest {
    @Test fun unknownIsNeutralAndGradientIsContinuous() {
        assertNotEquals(riskColor(null), riskColor(0.0))
        assertEquals(riskColor(null), riskColor(Double.NaN))
        assertTrue(riskColor(0.0).green > riskColor(0.0).red)
        assertTrue(riskColor(100.0).red > riskColor(100.0).green)
        for (edge in listOf(20.0, 40.0, 60.0, 80.0)) {
            val a = riskColor(edge - 0.01); val b = riskColor(edge + 0.01)
            assertTrue(kotlin.math.abs(a.red - b.red) < 0.01f)
            assertTrue(kotlin.math.abs(a.green - b.green) < 0.01f)
        }
    }
}
