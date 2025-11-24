import pytest
from django.urls import reverse

@pytest.mark.django_db
class TestBlogViews:
    def test_post_list_view(self, client, post_factory):
        """Test if the post list page loads and displays posts."""
        post = post_factory(title="Hello World")
        url = reverse('blog:post_list')
        
        response = client.get(url)
        
        assert response.status_code == 200
        assert "Hello World" in response.content.decode()
        assert "Tech Blog" in response.content.decode()

    def test_post_detail_view(self, client, post_factory):
        """Test if the post detail page loads."""
        post = post_factory(title="Detail Test", body_markdown="# Content")
        url = reverse('blog:post_detail', kwargs={'slug': post.slug})
        
        response = client.get(url)
        
        assert response.status_code == 200
        assert "Detail Test" in response.content.decode()
        # Check if markdown was converted to HTML (Markdown adds ids by default)
        assert '<h1 id="content">Content</h1>' in response.content.decode()
