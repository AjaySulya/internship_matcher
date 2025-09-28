import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple
import os

MODEL_FILENAME = "vectorizer.joblib"

class Recommender:
    def __init__(self):
        self.vectorizer = None
        self.internship_vectors = None
        self.internship_data = []

    def fit(self, internship_data: List[dict]):
        texts = []
        for internship in internship_data:
            skills = " ".join(internship.get("skills_required", []))
            text = f"{internship.get('role', '')} {internship.get('company_name', '')} {skills}".strip().lower()
            if not text:
                print(f"Skipping internship id {internship.get('internship_id')} with empty text")
                continue
            texts.append(text)
        if not texts:
            raise ValueError("No valid internship text documents found for vectorization. Please check your internship data.")
        print("Sample texts for vectorizer:", texts[:3])
        self.vectorizer = TfidfVectorizer()
        self.internship_vectors = self.vectorizer.fit_transform(texts)
        self.internship_data = internship_data

    def save(self, filepath: str = MODEL_FILENAME):
        joblib.dump({
            'vectorizer': self.vectorizer,
            'internship_vectors': self.internship_vectors,
            'internship_data': self.internship_data,
        }, filepath)

    def load(self, filepath: str = MODEL_FILENAME):
        if os.path.exists(filepath):
            data = joblib.load(filepath)
            self.vectorizer = data['vectorizer']
            self.internship_vectors = data['internship_vectors']
            self.internship_data = data['internship_data']
        else:
            raise FileNotFoundError(f"{filepath} does not exist")

    def recommend_internships(self, student_profile: dict, top_n: int = 5) -> List[dict]:
        # Create a text representation of student skills + resume text
        skills_text = " ".join(student_profile["skills"])
        resume_text = student_profile.get("resume_text", "")
        student_text = f"{skills_text} {resume_text}".lower()

        student_vector = self.vectorizer.transform([student_text])

        # Cosine similarity with internship vectors
        similarity_scores = cosine_similarity(student_vector, self.internship_vectors).flatten()

        # Additional scoring based on location and internship type preference
        def score_fn(idx):
            internship = self.internship_data[idx]
            score = similarity_scores[idx]

            # Location match bonus
            if internship["location"].lower() == student_profile["location"].lower():
                score += 0.1
            # Internship type preference match bonus
            if internship["intern_type"].lower() == student_profile["preferred_internship_type"].lower():
                score += 0.1
            elif internship["intern_type"].lower() == "hybrid" or student_profile["preferred_internship_type"].lower() == "hybrid":
                score += 0.05

            return score

        scored = [(idx, score_fn(idx)) for idx in range(len(self.internship_data))]
        scored_sorted = sorted(scored, key=lambda x: x[1], reverse=True)[:top_n]

        return [self.internship_data[idx] for idx, score in scored_sorted]

    def match_candidates(self, internship_profile: dict, students_data: List[dict], top_n: int = 5) -> List[dict]:
        # Vectorize student profiles and rank by similarity to internship profile
        if self.vectorizer is None:
            raise ValueError("Model not loaded or trained.")

        internship_text = f"{internship_profile['role']} {' '.join(internship_profile['skills_required'])}".lower()
        internship_vector = self.vectorizer.transform([internship_text])

        candidates_scores = []
        for student in students_data:
            student_text = f"{' '.join(student['skills'])} {student.get('resume_text', '')}".lower()
            student_vector = self.vectorizer.transform([student_text])

            similarity = cosine_similarity(internship_vector, student_vector).flatten()[0]

            # Location and internship type preference bonuses
            score = similarity
            if student["location"].lower() == internship_profile["location"].lower():
                score += 0.1
            if student["preferred_internship_type"].lower() == internship_profile["intern_type"].lower():
                score += 0.1
            elif internship_profile["intern_type"].lower() == "hybrid" or student["preferred_internship_type"].lower() == "hybrid":
                score += 0.05

            candidates_scores.append((student, score))

        candidates_scores.sort(key=lambda x: x[1], reverse=True)

        return [candidate for candidate, _ in candidates_scores[:top_n]]
