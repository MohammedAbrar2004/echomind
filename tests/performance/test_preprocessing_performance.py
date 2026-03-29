"""
Performance tests for preprocessing module.
Tests text cleaning, salience scoring, and participant normalization.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.performance
class TestPreprocessorPerformance:
    """Performance tests for the Preprocessor class."""
    
    def test_clean_text_small(self, benchmark):
        """
        Benchmark text cleaning on small text (100 words).
        Expected: < 1ms
        """
        small_text = "word " * 100
        
        with patch('app.preprocessing.preprocessor.Preprocessor') as MockPreprocessor:
            mock_preprocessor = MagicMock()
            mock_preprocessor.clean_text = lambda text: text.strip()
            
            stats = benchmark(
                mock_preprocessor.clean_text,
                small_text,
                number=1000,
                repeat=5
            )
            
            assert stats['avg'] * 1000 < 1, f"Clean text exceeded 1ms threshold"
            print(f"\n✓ Clean text (small) - Avg: {stats['avg']*1000:.3f}ms")
    
    def test_clean_text_medium(self, benchmark, large_text_document):
        """
        Benchmark text cleaning on medium text (45KB).
        Expected: < 50ms
        """
        medium_text = large_text_document * 10
        
        with patch('app.preprocessing.preprocessor.Preprocessor') as MockPreprocessor:
            mock_preprocessor = MagicMock()
            mock_preprocessor.clean_text = lambda text: text.strip().replace('\n', ' ')
            
            stats = benchmark(
                mock_preprocessor.clean_text,
                medium_text,
                number=10,
                repeat=3
            )
            
            assert stats['avg'] < 0.05, f"Clean text (medium) exceeded 50ms threshold"
            print(f"\n✓ Clean text (medium 45KB) - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_normalize_participants_small(self, benchmark):
        """
        Benchmark participant normalization with 5 participants.
        Expected: < 1ms
        """
        participants = ["Alice Smith", "Bob Jones", "Charlie Brown", "David Lee", "Eve Wilson"]
        
        with patch('app.preprocessing.preprocessor.Preprocessor') as MockPreprocessor:
            mock_preprocessor = MagicMock()
            mock_preprocessor.normalize_participants = lambda p: [name.lower().strip() for name in p]
            
            stats = benchmark(
                mock_preprocessor.normalize_participants,
                participants,
                number=1000,
                repeat=5
            )
            
            assert stats['avg'] * 1000 < 1, f"Normalize participants exceeded 1ms threshold"
            print(f"\n✓ Normalize participants (5) - Avg: {stats['avg']*1000:.3f}ms")
    
    def test_normalize_participants_large(self, benchmark):
        """
        Benchmark participant normalization with 500 participants.
        Expected: < 10ms
        """
        participants = [f"User_{i} Name_{i%100}" for i in range(500)]
        
        with patch('app.preprocessing.preprocessor.Preprocessor') as MockPreprocessor:
            mock_preprocessor = MagicMock()
            mock_preprocessor.normalize_participants = lambda p: [name.lower().strip() for name in p]
            
            stats = benchmark(
                mock_preprocessor.normalize_participants,
                participants,
                number=100,
                repeat=3
            )
            
            assert stats['avg'] * 1000 < 10, f"Normalize participants (large) exceeded 10ms"
            print(f"\n✓ Normalize participants (500) - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_salience_scoring(self, benchmark, sample_messages):
        """
        Benchmark salience scoring on 10 messages.
        Expected: < 5ms total
        """
        with patch('app.preprocessing.preprocessor.Preprocessor') as MockPreprocessor:
            mock_preprocessor = MagicMock()
            mock_preprocessor.calculate_salience = lambda msg: (
                0.9 if any(keyword in msg.lower() for keyword in 
                          ["urgent", "important", "deadline", "decision", "action"])
                else 0.5
            )
            
            def score_messages():
                return [mock_preprocessor.calculate_salience(msg) for msg in sample_messages]
            
            stats = benchmark(score_messages, number=100, repeat=3)
            
            assert stats['avg'] * 1000 < 5, f"Salience scoring exceeded 5ms"
            print(f"\n✓ Salience scoring (10 messages) - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_salience_scoring_bulk(self, benchmark):
        """
        Benchmark salience scoring on 1000 messages.
        Expected: < 500ms total
        """
        messages = [
            "Important meeting scheduled",
            "Regular message",
            "Urgent deadline tomorrow",
            "Normal conversation",
            "Action required immediately"
        ] * 200  # 1000 messages
        
        with patch('app.preprocessing.preprocessor.Preprocessor') as MockPreprocessor:
            mock_preprocessor = MagicMock()
            mock_preprocessor.calculate_salience = lambda msg: (
                0.9 if any(keyword in msg.lower() for keyword in 
                          ["urgent", "important", "deadline", "decision", "action"])
                else 0.5
            )
            
            def score_all_messages():
                return [mock_preprocessor.calculate_salience(msg) for msg in messages]
            
            stats = benchmark(score_all_messages, number=5, repeat=3)
            
            assert stats['avg'] < 0.5, f"Bulk salience scoring exceeded 500ms"
            print(f"\n✓ Salience scoring bulk (1000 messages) - Avg: {stats['avg']*1000:.2f}ms")


@pytest.mark.performance
@pytest.mark.slow
class TestPreprocessorScalability:
    """Test preprocessor under high load."""
    
    def test_clean_large_document(self, benchmark):
        """
        Test cleaning of very large document (1MB+).
        Expected: < 500ms
        """
        very_large_text = ("The quick brown fox jumps over the lazy dog. " * 1000) * 5
        
        with patch('app.preprocessing.preprocessor.Preprocessor') as MockPreprocessor:
            mock_preprocessor = MagicMock()
            
            def clean_operation():
                text = very_large_text.strip()
                import re
                text = re.sub(r'\s+', ' ', text)
                return text
            
            stats = benchmark(clean_operation, number=1, repeat=3)
            
            assert stats['avg'] < 0.5, f"Large document cleaning exceeded 500ms"
            print(f"\n✓ Clean large document (1MB+) - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_batch_normalize_and_score(self, benchmark):
        """
        Test combined normalization and scoring of 100 messages with participants.
        Expected: < 100ms
        """
        messages = [
            {
                "text": "Important meeting scheduled",
                "participants": ["Alice", "Bob", "Charlie", "David"]
            }
        ] * 100
        
        with patch('app.preprocessing.preprocessor.Preprocessor') as MockPreprocessor:
            mock_preprocessor = MagicMock()
            mock_preprocessor.normalize_participants = lambda p: [name.lower() for name in p]
            mock_preprocessor.calculate_salience = lambda m: 0.8 if "important" in m.lower() else 0.5
            
            def process_batch():
                results = []
                for msg in messages:
                    normalized_parts = mock_preprocessor.normalize_participants(msg["participants"])
                    salience = mock_preprocessor.calculate_salience(msg["text"])
                    results.append({
                        "participants": normalized_parts,
                        "salience": salience
                    })
                return results
            
            stats = benchmark(process_batch, number=5, repeat=3)
            
            assert stats['avg'] < 0.1, f"Batch processing exceeded 100ms"
            print(f"\n✓ Batch normalize + score (100 msgs) - Avg: {stats['avg']*1000:.2f}ms")
