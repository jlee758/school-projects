/**
* @author See Contributors.txt for code contributors and overview of BadgerDB.
* Jay Hwan Lee (9074934606)
* Jong Hoon Kim (9068361055)
* Yicheng Lin (9069739374)
*
* @Description
* Contains all the implemented methods for the project. Handles buffer management and buffer pools.
* Unpins pages, flushes dirty pages, and uses the clock algorithm to allocate buffer frames.
*
* @section LICENSE
* Copyright (c) 2012 Database Group, Computer Sciences Department, University of Wisconsin-Madison.
*/

#include <memory>
#include <iostream>
#include "buffer.h"
#include "exceptions/buffer_exceeded_exception.h"
#include "exceptions/page_not_pinned_exception.h"
#include "exceptions/page_pinned_exception.h"
#include "exceptions/bad_buffer_exception.h"
#include "exceptions/hash_not_found_exception.h"

namespace badgerdb {

	BufMgr::BufMgr(std::uint32_t bufs)
	: numBufs(bufs) {
		bufDescTable = new BufDesc[bufs];

		for (FrameId i = 0; i < bufs; i++)
		{
			bufDescTable[i].frameNo = i;
			bufDescTable[i].valid = false;
		}

		bufPool = new Page[bufs];

		int htsize = ((((int) (bufs * 1.2))*2)/2)+1;
		hashTable = new BufHashTbl (htsize);  // allocate the buffer hash table

		clockHand = bufs - 1;
	}

	BufMgr::~BufMgr() {
		//flush out dirty pages
		for(std::uint32_t i = 0; i < numBufs; i++) {
			if(bufDescTable[i].dirty) {
				flushFile(bufDescTable[i].file);
			}
		}

		//deallocate pool and table
		delete[] bufPool;
		delete[] bufDescTable;
	}

	void BufMgr::advanceClock()
	{
		//advance clock to next frame in the buffer pool
		clockHand++;
		clockHand = clockHand % numBufs;
	}

	void BufMgr::allocBuf(FrameId & frame)
	{
		std::uint32_t num = 0;
		bool checkFoundFrame = false;

		//use clock algorithm
		while(num <= numBufs) {
			num++;
			advanceClock();

			//check if valid
			if(!bufDescTable[clockHand].valid) {
				checkFoundFrame = true;
				break;
				//check if refbit set
			} else if (bufDescTable[clockHand].refbit) {
				bufDescTable[clockHand].refbit = false;
				continue;
				//check if pinned
			} else if (bufDescTable[clockHand].pinCnt > 0) {
				continue;
			} else {
				//flushFile handles all the relevant work
				flushFile(bufDescTable[clockHand].file);

				checkFoundFrame = true;
				break;
			}
		}

		//throw exception if all frames pinned
		if(!checkFoundFrame && (num > numBufs)) {
			throw BufferExceededException();
		}

		//return frame
		frame = clockHand;
		bufDescTable[clockHand].Clear();
	}

	void BufMgr::readPage(File* file, const PageId pageNo, Page*& page)
	{
		//will hold the frame number
		FrameId frame;

		try {
			//throws HashNotFoundException if page is not in buffer pool
			hashTable->lookup(file, pageNo, frame);

			//Page is in buffer pool:
			//returns pointer to the page after modifying it
			bufDescTable[frame].refbit = true;
			bufDescTable[frame].pinCnt++;
			page = &bufPool[frame];
		} catch (HashNotFoundException e) {
			//Page not in buffer pool:
			//read page from disk into allocated buffer pool frame, then insert into hash table
			allocBuf(frame);
			bufPool[frame] = file->readPage(pageNo);
			hashTable->insert(file, pageNo, frame);
			bufDescTable[frame].Set(file, pageNo);
			page = &bufPool[frame];
		}
	}

	void BufMgr::unPinPage(File* file, const PageId pageNo, const bool dirty)
	{
		FrameId frame;

		hashTable->lookup(file, pageNo, frame);

		//Throw PageNotPinned if there is no pin count to decrement
		if(bufDescTable[frame].pinCnt == 0) {
			throw PageNotPinnedException(file->filename(), pageNo, frame);
		} else {
		//decrement the pin count
			bufDescTable[frame].pinCnt--;
		}

		//set the dirty bit if necessary
		if(dirty) {
			bufDescTable[frame].dirty = true;
		}
	}

	void BufMgr::flushFile(const File* file)
	{
		for(std::uint32_t i = 0; i < numBufs; i++) {
			//checks if the page belongs to the file
			if((bufDescTable[i].file == file) && bufDescTable[i].valid) {

				//If page is pinned, throw exception
				if(bufDescTable[i].pinCnt > 0) {
					throw PagePinnedException(file->filename(), bufDescTable[i].pageNo,
					bufDescTable[i].frameNo);
				}

				//if the page is dirty, flush it to disk and set dirty bit to false
				if(bufDescTable[i].dirty) {
					bufDescTable[i].dirty = false;
					bufDescTable[i].file->writePage(bufPool[bufDescTable[i].frameNo]);
				}

				//remove and clear page
				hashTable->remove(bufDescTable[i].file, bufDescTable[i].pageNo);
				bufDescTable[i].Clear();
			} else if ((bufDescTable[i].file == file) && !bufDescTable[i].valid) {
				//If invalid page belongs to file, throw exception
				throw BadBufferException(i, bufDescTable[i].dirty, bufDescTable[i].valid,
					bufDescTable[i].refbit);
			}
		}
	}

	void BufMgr::allocPage(File* file, PageId &pageNo, Page*& page)
	{
		//allocate empty page
		Page newPage = file->allocatePage();

		//obtain buffer pool frame
		FrameId frame = 0;
		allocBuf(frame);
		bufPool[frame] = newPage;

		//Insert into hash table, set the frame
		hashTable->insert(file, newPage.page_number(), frame);
		bufDescTable[frame].Set(file, newPage.page_number());

		//return page number and buffer frame pointer
		page = &bufPool[frame];
		pageNo = newPage.page_number();
	}

	void BufMgr::disposePage(File* file, const PageId PageNo)
	{
		FrameId frame;

		hashTable->lookup(file, PageNo, frame);

		//frees frame and entry from hash table if allocated a frame in buffer pool
		bufDescTable[frame].Clear();
		hashTable->remove(file, PageNo);

		//deletes the page from the file
		file->deletePage(PageNo);
	}

	void BufMgr::printSelf(void)
	{
		BufDesc* tmpbuf;
		int validFrames = 0;

		for (std::uint32_t i = 0; i < numBufs; i++)
		{
			tmpbuf = &(bufDescTable[i]);
			std::cout << "FrameNo:" << i << " ";
			tmpbuf->Print();

			if (tmpbuf->valid == true)
			validFrames++;
		}

		std::cout << "Total Number of Valid Frames:" << validFrames << "\n";
	}
}
