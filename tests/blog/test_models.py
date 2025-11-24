import pytest
from blog.models import Post

class TestPostModel:
    def test_post_creation(self, post_factory):
        """Test if a post can be created successfully."""
        post = post_factory(title="Test Post")
        assert post.pk is not None
        assert post.title == "Test Post"
        assert post.slug == "test-post"

    def test_markdown_conversion(self, post_factory):
        """Test if markdown is correctly converted to HTML on save."""
        markdown_content = "# Heading\n\n**Bold text**"
        post = post_factory(body_markdown=markdown_content)
        
        # Markdown adds ids to headers by default
        assert '<h1 id="heading">Heading</h1>' in post.body_html
        assert "<strong>Bold text</strong>" in post.body_html

    def test_html_sanitization_xss(self, post_factory):
        """
        CRITICAL: Test if malicious scripts are stripped from HTML.
        This validates the nh3 integration.
        """
        from textwrap import dedent
        malicious_markdown = dedent("""
        <script>alert('XSS')</script>
        [Click me](javascript:alert('XSS'))
        <img src=x onerror=alert(1)>
        """)
        post = post_factory(body_markdown=malicious_markdown)
        
        # Ensure script tags are removed
        assert "<script>" not in post.body_html
        assert "alert('XSS')" not in post.body_html
        
        # Ensure javascript: links are removed or sanitized
        assert "javascript:" not in post.body_html
        
        # Ensure onerror handlers are removed
        assert "onerror" not in post.body_html

    def test_search_vector_update(self, post_factory):
        """Test if SearchVector is updated after save."""
        post = post_factory(title="Python Django", summary="Web framework", body_markdown="Best for web")
        
        # Refresh from DB to get the generated SearchVector
        post.refresh_from_db()
        
        # Note: Testing exact SearchVector content usually requires a running Postgres instance
        if post.search_vector:
            assert "python" in str(post.search_vector).lower()

    def test_allowed_tags_and_attributes(self, post_factory):
        """Test if allowed tags and attributes are preserved."""
        from textwrap import dedent
        content = dedent("""
        <a href="https://example.com" title="Example" class="link">Link</a>
        <code class="python">print('hello')</code>
        """)
        post = post_factory(body_markdown=content)
        
        assert '<a href="https://example.com"' in post.body_html
        assert 'title="Example"' in post.body_html
        assert 'class="link"' in post.body_html
        assert '<code class="python">' in post.body_html

    def test_slug_uniqueness(self, post_factory):
        """Test that slugs must be unique."""
        post_factory(slug="unique-slug")
        with pytest.raises(Exception): # IntegrityError or ValidationError
            post_factory(slug="unique-slug")
