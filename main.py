#!/usr/bin/env python3.10

import argparse
import sqlite3
from dataclasses import dataclass
from enum import Enum

DATABASE = '/path/to/database.betula'

session = sqlite3.connect(":memory:")


class Visibility(int, Enum):
    Private = 0
    Public = 1

    @classmethod
    def from_string(cls, vis: str) -> 'Visibility':
        if vis == 'private':
            return cls.Private
        return cls.Public


@dataclass
class Category:
    Name: str
    PostCount: int = 0


@dataclass
class Post:
    # URL is a URL with any protocol.
    URL: str
    # Title is a name for the link.
    Title: str
    # Description is a Mycomarkup-formatted document. Currently, just unescaped plain text.
    Description: str
    # Visibility sets who can see the post.
    Visibility: Visibility
    # Categories are categories of this post. Do not set this field by yourself.
    Categories: list[Category]
    # ID is a unique identifier of the post. Do not set this field by yourself.
    ID: int | None = None
    # CreationTime is UNIX seconds. Do not set this field by yourself.
    CreationTime: int | None = None


class DB:
    def __init__(self):
        self.session = sqlite3.connect(DATABASE)

    def execute(self, query: str, *args, many=False, **kwargs) -> sqlite3.Cursor:
        cursor = self.session.cursor()
        func = cursor.executemany if many else cursor.execute
        func(query, *args, **kwargs)
        session.commit()
        return cursor

    def create_post(self, post: Post) -> None:
        post.ID = self.execute(
            'insert into Posts (URL, Title, Description, Visibility) values (?, ?, ?, ?)',
            (post.URL, post.Title, post.Description, post.Visibility),
        ).lastrowid
        if post.ID is None:
            raise Exception('Can not create post')

        if post.Categories:
            self.create_categories(post.Categories, post.ID)

    def create_categories(self, cats: list[Category], post_id: int) -> None:
        self.execute(
            'insert into CategoriesToPosts (CatName, PostID) values (?, ?)',
            ((c.Name, post_id) for c in cats),
            many=True,
        )


def create_post(args: argparse.Namespace) -> None:
    db = DB()
    db.create_post(
        Post(
            URL=args.url,
            Title=args.title,
            Description=args.description,
            Visibility=Visibility.Private if args.private else Visibility.Public,
            Categories=[Category(Name=c) for c in args.categories],
        )
    )


if __name__ == '__main__':
    main_parser = argparse.ArgumentParser()
    subparsers = main_parser.add_subparsers(required=True)

    post_parser = subparsers.add_parser('add')
    post_parser.add_argument('url')
    post_parser.add_argument('title')
    post_parser.add_argument('--description', '-d', default='')
    post_parser.add_argument('--private', '-p', action='store_true')
    post_parser.add_argument('--categories', '-c', nargs='*', default=[])
    post_parser.set_defaults(func=create_post)

    namespace = main_parser.parse_args()
