package com.tomatocare

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.tomatocare.data.model.DiagnosisResult
import com.tomatocare.data.model.GrowingMethod
import com.tomatocare.data.model.ScanRecord
import com.tomatocare.data.model.SeverityLevel
import com.tomatocare.data.model.StressType
import com.tomatocare.data.storage.ScanStorageManager
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

@RunWith(AndroidJUnit4::class)
class ScanStorageManagerTest {

    private lateinit var storage: ScanStorageManager
    private lateinit var filesDir: File

    @Before
    fun setUp() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        filesDir = context.filesDir
        storage = ScanStorageManager(context)
        // Clean slate for each test
        runBlocking { storage.deleteAll() }
    }

    @After
    fun tearDown() {
        runBlocking { storage.deleteAll() }
    }

    private fun makeRecord(id: Int = 0, confidence: Double = 0.95) = ScanRecord(
        scanId = id,
        imagePath = "/data/user/0/com.tomatocare/files/img_$id.jpg",
        timestamp = "2026-05-12T10:00:00Z",
        growingMethod = GrowingMethod.OPEN_FIELD,
        modelVersion = "1.0.0",
        results = listOf(
            DiagnosisResult(
                resultId = 1,
                conditionId = "tomato_late_blight",
                conditionNameEn = "Late Blight",
                conditionNameAr = "اللفحة المتأخرة",
                confidence = confidence,
                isPrimary = true,
                stressType = StressType.BIOTIC,
                severityLevel = SeverityLevel.CRITICAL,
            )
        ),
    )

    @Test
    fun loadAll_empty_returnsEmptyList() = runBlocking {
        assertTrue(storage.loadAll().isEmpty())
    }

    @Test
    fun saveRecord_assignsAutoIncrementId() = runBlocking {
        storage.saveRecord(makeRecord(id = 0))
        val all = storage.loadAll()
        assertEquals(1, all.size)
        assertEquals(1, all[0].scanId)
    }

    @Test
    fun saveRecord_multipleRecords_newestFirst() = runBlocking {
        storage.saveRecord(makeRecord())
        storage.saveRecord(makeRecord())
        storage.saveRecord(makeRecord())
        val all = storage.loadAll()
        assertEquals(3, all.size)
        // IDs should be 3, 2, 1 (newest prepended)
        assertEquals(3, all[0].scanId)
        assertEquals(2, all[1].scanId)
        assertEquals(1, all[2].scanId)
    }

    @Test
    fun getById_returnsCorrectRecord() = runBlocking {
        storage.saveRecord(makeRecord(confidence = 0.91))
        storage.saveRecord(makeRecord(confidence = 0.76))
        val all = storage.loadAll()
        val id = all[1].scanId  // older record
        val found = storage.getById(id)
        assertNotNull(found)
        assertEquals(0.76, found!!.results[0].confidence, 0.001)
    }

    @Test
    fun getById_missingId_returnsNull() = runBlocking {
        assertNull(storage.getById(999))
    }

    @Test
    fun deleteById_removesOnlyTargetRecord() = runBlocking {
        storage.saveRecord(makeRecord())
        storage.saveRecord(makeRecord())
        val all = storage.loadAll()
        val toDelete = all[1].scanId
        val deleted = storage.deleteById(toDelete)
        assertTrue(deleted)
        val remaining = storage.loadAll()
        assertEquals(1, remaining.size)
        assertNull(remaining.firstOrNull { it.scanId == toDelete })
    }

    @Test
    fun deleteById_nonExistentId_returnsFalse() = runBlocking {
        assertFalse(storage.deleteById(999))
    }

    @Test
    fun deleteAll_clearsStorage() = runBlocking {
        storage.saveRecord(makeRecord())
        storage.saveRecord(makeRecord())
        storage.deleteAll()
        assertTrue(storage.loadAll().isEmpty())
    }

    @Test
    fun replaceAll_overwritesExistingHistory() = runBlocking {
        storage.saveRecord(makeRecord())
        storage.saveRecord(makeRecord())
        val replacement = listOf(makeRecord(id = 10), makeRecord(id = 11))
        storage.replaceAll(replacement)
        val all = storage.loadAll()
        assertEquals(2, all.size)
        assertEquals(10, all[0].scanId)
        assertEquals(11, all[1].scanId)
    }

    @Test
    fun atomicWrite_noCorruptFileLeft() = runBlocking {
        storage.saveRecord(makeRecord())
        // Temp file must not linger after a successful write
        val tmpFile = File(filesDir, "scan_history.tmp")
        assertFalse("Temp file should not exist after successful write", tmpFile.exists())
    }
}
