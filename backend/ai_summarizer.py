# backend/ai_summarizer.py - CORRECTED TO MATCH KAGGLE VERSION
import time
import re
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

# NLP libraries
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class GermanDocumentSummarizer:
    """
    German Document AI Summarizer - CORRECTED TO MATCH KAGGLE
    Uses German-optimized models for professional document summarization
    """

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.model_loaded = False

        if TRANSFORMERS_AVAILABLE:
            self._initialize_model()
        else:
            logger.warning("Transformers not available. AI summarization will use fallback mode.")

    def _initialize_model(self):
        """Initialize German summarization model"""
        try:
            logger.info("Loading German AI summarization model...")

            # Set device
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Using device: {self.device}")

            # Use the same model from your Kaggle code
            model_name = "ml6team/mt5-small-german-finetune-mlsum"

            # Initialize with pipeline for simplicity
            self.summarizer = pipeline(
                "summarization",
                model=model_name,
                tokenizer=model_name,
                device=0 if torch.cuda.is_available() else -1
            )

            self.model_loaded = True
            logger.info("German AI model loaded successfully!")

        except Exception as e:
            logger.error(f"Failed to load AI model: {e}")
            self.model_loaded = False

    def is_model_loaded(self):
        """Check if AI model is ready"""
        return self.model_loaded

    def generate_summary(self, cleaned_text):
        """
        Generate professional German summary - CORRECTED VERSION

        Args:
            cleaned_text (str): Preprocessed German text from PDF

        Returns:
            dict: Summary result with formatted output
        """
        try:
            logger.info("Generating German document summary...")
            start_time = time.time()

            if not cleaned_text or len(cleaned_text.strip()) < 50:
                return {"success": False, "error": "Text too short for summarization"}

            # Extract structured information (your method)
            extracted_info = self._extract_document_information(cleaned_text)

            # Generate AI summary with ORIGINAL method from Kaggle
            if self.model_loaded:
                ai_summaries = self._generate_ai_summary_kaggle_version(cleaned_text)
            else:
                ai_summaries = self._generate_fallback_summary(cleaned_text)

            # Format professional German summary (your formatting)
            formatted_summary = self._format_professional_german_summary(extracted_info, ai_summaries)

            processing_time = time.time() - start_time
            word_count = len(formatted_summary.split())

            # Calculate quality score
            quality_score = self._calculate_quality_score(formatted_summary, extracted_info)

            result = {
                "success": True,
                "formatted_summary": formatted_summary,
                "extracted_info": extracted_info,
                "ai_summaries": ai_summaries,
                "stats": {
                    "processing_time": round(processing_time, 2),
                    "word_count": word_count,
                    "quality_score": quality_score,
                    "model_used": "AI" if self.model_loaded else "Fallback"
                },
                "quality_score": quality_score,
                "word_count": word_count
            }

            logger.info(f"Summary generated: {word_count} words, quality: {quality_score}%")
            return result

        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return {"success": False, "error": str(e)}

    def _extract_document_information(self, text):
        """
        Extract structured information from German document - ORIGINAL KAGGLE VERSION
        """
        info = {}

        # Document type detection
        doc_types = {
            'Vereinsregister': r'Vereinsregister|Register.*Verein',
            'Handelsregister': r'Handelsregister|Register.*Handel',
            'Gerichtsdokument': r'Amtsgericht|Landgericht|Gerichtshof',
            'Vertrag': r'Vertrag|Vereinbarung|Kontrakt',
            'Bescheid': r'Bescheid|Mitteilung|Benachrichtigung'
        }

        for doc_type, pattern in doc_types.items():
            if re.search(pattern, text, re.IGNORECASE):
                info['document_type'] = doc_type
                break
        else:
            info['document_type'] = 'Deutsches Dokument'

        # Organization/Company names (flexible patterns)
        org_patterns = [
            r'([A-Za-zäöüßÄÖÜ\s&-]+)\s*e\.V\.',
            r'([A-Za-zäöüßÄÖÜ\s&-]+)\s*GmbH',
            r'([A-Za-zäöüßÄÖÜ\s&-]+)\s*AG',
            r'([A-Za-zäöüßÄÖÜ\s&-]+)\s*KG',
            r'([A-Za-zäöüßÄÖÜ\s&-]+)\s*GbR',
            r'Name[:\s]*([A-Za-zäöüßÄÖÜ\s&-]+)',
            r'Firma[:\s]*([A-Za-zäöüßÄÖÜ\s&-]+)',
            r'a\)\s*([A-Za-zäöüßÄÖÜ\s&-]+)'
        ]

        for pattern in org_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                org_name = max(matches, key=len).strip()
                if len(org_name) > 5:
                    info['organization'] = org_name
                    break

        # Registry/Reference numbers
        number_patterns = [
            r'VR\s*(\d+)',
            r'HRB\s*(\d+)',
            r'HRA\s*(\d+)',
            r'Nummer[:\s]*(\d+)',
            r'Aktenzeichen[:\s]*([A-Za-z0-9\s/-]+)',
        ]

        for pattern in number_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['reference_number'] = match.group(0).strip()
                break

        # Location information
        location_patterns = [
            r'b\)\s*([A-Za-zäöüßÄÖÜ-]+)',
            r'Sitz[:\s]*([A-Za-zäöüßÄÖÜ-]+)',
            r'Ort[:\s]*([A-Za-zäöüßÄÖÜ-]+)',
            r'Amtsgericht\s+([A-Za-zäöüßÄÖÜ-]+)',
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                info['location'] = match.group(1).strip()
                break

        # Important dates with German formatting
        date_pattern = r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
        dates_raw = re.findall(date_pattern, text)
        if dates_raw:
            formatted_dates = []
            for day, month, year in dates_raw:
                try:
                    datetime(int(year), int(month), int(day))
                    german_months = {
                        '01': 'Januar', '02': 'Februar', '03': 'März', '04': 'April',
                        '05': 'Mai', '06': 'Juni', '07': 'Juli', '08': 'August',
                        '09': 'September', '10': 'Oktober', '11': 'November', '12': 'Dezember'
                    }
                    formatted_date = f"{int(day)}. {german_months.get(month.zfill(2), month)} {year}"
                    formatted_dates.append(formatted_date)
                except:
                    pass

            if formatted_dates:
                info['important_dates'] = list(set(formatted_dates))

        # People names
        name_patterns = [
            r'([A-Za-zäöüßÄÖÜ]+,\s*[A-Za-zäöüßÄÖÜ]+(?:\s*[A-Za-zäöüßÄÖÜ]+)?)',
            r'Dr\.\s+([A-Za-zäöüßÄÖÜ,\s]+)',
        ]

        all_names = []
        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            all_names.extend(matches)

        if all_names:
            clean_names = []
            for name in all_names:
                name = name.strip()
                if len(name) > 5 and ',' in name:
                    clean_names.append(name)

            if clean_names:
                info['persons'] = list(set(clean_names[:5]))

        # Key roles
        role_patterns = [
            r'(Vorsitzende[rn]?)',
            r'(Geschäftsführer[in]?)',
            r'(Vorstand)',
            r'(Direktor[in]?)',
            r'(Prokurist[in]?)'
        ]

        roles = []
        for pattern in role_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            roles.extend(matches)

        if roles:
            info['roles'] = list(set(roles))

        return info

    def _generate_ai_summary_kaggle_version(self, text):
        """
        CORRECTED: Generate AI summaries using your ORIGINAL Kaggle method
        """
        try:
            # Create sophisticated German prompt (ORIGINAL from Kaggle)
            prompt_template = '''Erstelle eine professionelle Zusammenfassung dieses deutschen Dokuments:

{text_chunk}

Strukturiere die wichtigsten Informationen:
- Hauptinhalt und Zweck des Dokuments
- Beteiligte Personen und Organisationen
- Wichtige Daten und Fristen
- Änderungen oder Beschlüsse
- Rechtliche Relevanz

Verwende einen sachlichen, professionellen Stil.'''

            # Process text in chunks
            max_chunk = 800
            chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]

            summaries = []
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) > 100:
                    try:
                        # FIXED: Use .replace() instead of .format() to avoid parentheses issues
                        prompted_text = prompt_template.replace('{text_chunk}', chunk)

                        result = self.summarizer(
                            prompted_text,
                            max_length=150,
                            min_length=30,
                            do_sample=False,
                            early_stopping=True,
                            no_repeat_ngram_size=3
                        )

                        summary_text = result[0]['summary_text']
                        summaries.append(summary_text)

                    except Exception as e:
                        logger.warning(f"AI summary chunk {i} failed: {e}")
                        summaries.append(f"Abschnitt {i+1}: {chunk[:200]}...")

            return summaries

        except Exception as e:
            logger.error(f"AI summary generation failed: {e}")
            return self._generate_fallback_summary(text)

    def _generate_fallback_summary(self, text):
        """Generate fallback summary when AI is not available"""
        # Simple extraction-based summary
        sentences = text.split('.')
        important_sentences = []

        keywords = ['Verein', 'GmbH', 'AG', 'Vorstand', 'Geschäftsführer', 'Eintragung', 'Änderung']

        for sentence in sentences:
            if any(keyword in sentence for keyword in keywords):
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 20:
                    important_sentences.append(clean_sentence)

        return important_sentences[:5]  # Top 5 important sentences

    def _format_professional_german_summary(self, extracted_info, ai_summaries):
        """
        Format professional German summary - ORIGINAL KAGGLE FORMATTING
        """
        summary = "Hier finden Sie eine Zusammenfassung des bereitgestellten PDF-Dokuments:\n\n"
        summary += "Zusammenfassung der Dokumentdetails\n\n"
        summary += "Das Dokument bezieht sich auf:\n"

        # Basic information section
        if extracted_info.get('organization'):
            summary += f"Name: {extracted_info['organization']}\n\n"

        if extracted_info.get('reference_number'):
            summary += f"Nummer/Aktenzeichen: {extracted_info['reference_number']}\n\n"

        if extracted_info.get('location'):
            summary += f"Ort/Standort: {extracted_info['location']}\n\n"

        if extracted_info.get('important_dates'):
            if len(extracted_info['important_dates']) >= 2:
                summary += f"Tag der ersten Eintragung: {extracted_info['important_dates'][-1]}\n\n"
                summary += f"Datum der aktuellen Fassung: {extracted_info['important_dates'][0]}\n\n"
            else:
                summary += f"Wichtiges Datum: {extracted_info['important_dates'][0]}\n\n"

        # Key content section
        summary += "Wichtige Inhalte und Änderungen\n\n"

        for i, ai_summary in enumerate(ai_summaries):
            if ai_summary.strip():
                summary += f"Eintrag {i+1}:\n{ai_summary.strip()}\n\n"

        # People and roles section
        if extracted_info.get('persons') or extracted_info.get('roles'):
            summary += "Beteiligte Personen und Funktionen:\n\n"

            if extracted_info.get('persons'):
                for person in extracted_info['persons'][:3]:
                    summary += f"• {person}\n"

            if extracted_info.get('roles'):
                summary += f"\nFunktionen: {', '.join(extracted_info['roles'][:5])}\n"

        summary += f"\n---\nDokumenttyp: {extracted_info.get('document_type', 'Deutsches Dokument')}"

        return summary

    def _calculate_quality_score(self, summary, extracted_info):
        """Calculate quality score based on completeness"""
        score = 50  # Base score

        # Add points for extracted information
        if extracted_info.get('organization'):
            score += 15
        if extracted_info.get('reference_number'):
            score += 10
        if extracted_info.get('location'):
            score += 5
        if extracted_info.get('important_dates'):
            score += 10
        if extracted_info.get('persons'):
            score += 5
        if extracted_info.get('roles'):
            score += 5

        # Check summary length
        word_count = len(summary.split())
        if word_count > 50:
            score += min(10, word_count // 10)

        return min(100, score)

# Test function
def test_summarizer():
    """Test the summarizer with sample text"""
    summarizer = GermanDocumentSummarizer()

    sample_text = '''
    Vereinsregister des Amtsgerichts Mannheim
    Deutsche Morgan Horse Association e.V. (DMHA)
    VR 360599
    Sitz: Karlsbad
    Tag der ersten Eintragung: 13.09.1989
    Vorstand: Dr. Wiegand, Ursel, erste Vorsitzende
    Geschäftsführerin: Morange, Marita, Geldern
    '''

    result = summarizer.generate_summary(sample_text)

    if result["success"]:
        print("✅ Summarization successful")
        print(f"Quality: {result['stats']['quality_score']}%")
        print(f"Words: {result['stats']['word_count']}")
        print("\nSummary:")
        print(result["formatted_summary"])
    else:
        print(f"❌ Summarization failed: {result['error']}")

if __name__ == "__main__":
    test_summarizer()
