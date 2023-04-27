from requests import post, delete

print(delete('http://localhost:8080/api/news/3').json())