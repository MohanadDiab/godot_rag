.. _doc_test_coding:

Coding the player
=================

Start by declaring variables:

.. tabs::
 .. code-tab:: gdscript GDScript

    extends Area2D
    @export var speed = 400

 .. code-tab:: csharp

    using Godot;
    public partial class Player : Area2D { }

 .. code-tab:: cpp C++

    The C++ part of this tutorial wasn't rewritten for the new GDExtension system yet.

Using ``export`` allows Inspector editing.

Player movement
---------------

The ``_process()`` function runs every frame.
