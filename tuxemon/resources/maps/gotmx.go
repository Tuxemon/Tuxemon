package main

import (
	"fmt"
	"github.com/salviati/go-tmx/tmx"
	"os"
)

func main() {
	fmt.Println("vim-go")
	f, err := os.Open("bedroom_test.tmx")
	if err != nil {
		panic(err)
	}

	mapData, err := tmx.Read(f)
	if err != nil {
		panic(err)
	}
	fmt.Println(mapData.Version)
	fmt.Println(mapData.Tilesets)
	fmt.Println(mapData.Properties)
	for _, layer := range mapData.Layers {
		fmt.Println("Layer name:", layer.Name)
		fmt.Println("  Tileset:", layer.Tileset)
		fmt.Println("  Data:", layer.Data.DataTiles)
	}

	for _, tileset := range mapData.Tilesets {
		fmt.Println("Name:", tileset.Name)
		fmt.Println("  Tiles:", tileset.Tiles)
		fmt.Println("  Count:", tileset.Tilecount)
		fmt.Println("  FirstGID:", tileset.FirstGID)
	}
	fmt.Println("Decoded tile:", mapData.Layers[0].DecodedTiles[20].IsNil())
	fmt.Println("Decoded tile:", mapData.Layers[0].DecodedTiles[20].ID)
}
